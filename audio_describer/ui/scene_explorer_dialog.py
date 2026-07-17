# audio_describer/ui/scene_explorer_dialog.py
from ..i18n_setup import _
import math
import pygame

from ..utils.logger import app_logger
from .accessibility_utils import speak_message

class SceneExplorer:
    # FIX: The constructor now accepts the translation function `trans_func`
    def __init__(self, scene_data, trans_func):
        # Use the passed-in translation function and store it
        self._ = trans_func

        self.scene_data = scene_data
        
        self.grid_size = scene_data.get("grid_size", [10, 10])
        # Use the stored translation function to translate default strings
        self.overall_description = scene_data.get("overall_description", self._("No overall description was provided."))
        self.objects = scene_data.get("objects", [])

        self.user_pos = [self.grid_size[0] // 2, self.grid_size[1] // 2]
        
        self.mode = "explore"
        self.list_selection_index = 0

        self.running = False
        self.screen = None
        self.font = None
        self.clock = None

    def run(self):
        try:
            pygame.init()
            pygame.font.init()
            self.screen = pygame.display.set_mode((600, 400))
            pygame.display.set_caption(self._("Scene Explorer"))
            self.font = pygame.font.SysFont("Arial", 20)
            self.clock = pygame.time.Clock()
            
            self.running = True
            self.initial_announcement()
            
            while self.running:
                self.handle_events()
                self.draw()
                self.clock.tick(30)
        except Exception as e:
            app_logger.error(f"Error during Scene Explorer execution: {e}", exc_info=True)
            speak_message(self._("An error occurred in the Scene Explorer."), interrupt=True)
        finally:
            pygame.quit()
            app_logger.info("Scene Explorer closed and Pygame quit.")

    def initial_announcement(self):
        speak_message(self._("Scene Explorer opened. Use arrow keys to move. Press D for scene description, L to list all objects, and Shift + L to enter jump mode. Escape to close."), interrupt=True)
        self.announce_position()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.mode == "explore":
                    self.handle_explore_mode_keys(event)
                elif self.mode == "list":
                    self.handle_list_mode_keys(event)

    def handle_explore_mode_keys(self, event):
        moved = False
        if event.key == pygame.K_UP:
            self.user_pos[1] = max(0, self.user_pos[1] - 1)
            moved = True
        elif event.key == pygame.K_DOWN:
            self.user_pos[1] = min(self.grid_size[1] - 1, self.user_pos[1] + 1)
            moved = True
        elif event.key == pygame.K_LEFT:
            self.user_pos[0] = max(0, self.user_pos[0] - 1)
            moved = True
        elif event.key == pygame.K_RIGHT:
            self.user_pos[0] = min(self.grid_size[0] - 1, self.user_pos[0] + 1)
            moved = True
        elif event.key == pygame.K_RETURN:
            self.inspect_object()
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_d:
            self.read_overall_description()
        elif event.key == pygame.K_l:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                self.enter_list_mode()
            else:
                self.list_all_objects()

        if moved:
            self.announce_position()

    def handle_list_mode_keys(self, event):
        if not self.objects:
            self.exit_list_mode()
            return

        if event.key == pygame.K_UP:
            self.list_selection_index = max(0, self.list_selection_index - 1)
            self.announce_list_item()
        elif event.key == pygame.K_DOWN:
            self.list_selection_index = min(len(self.objects) - 1, self.list_selection_index + 1)
            self.announce_list_item()
        elif event.key == pygame.K_RETURN:
            self.jump_to_selected_object()
        elif event.key == pygame.K_ESCAPE:
            self.exit_list_mode()
            
    def enter_list_mode(self):
        if not self.objects:
            speak_message(self._("There are no objects to jump to."), interrupt=True)
            return
        
        self.mode = "list"
        self.list_selection_index = 0
        speak_message(self._("Jump mode. Use up and down arrows to select an object. Press Enter to jump, or Escape to exit jump mode."), interrupt=True)
        self.announce_list_item()

    def exit_list_mode(self):
        self.mode = "explore"
        speak_message(self._("Exited jump mode. Now exploring."), interrupt=True)
        self.announce_position()
        
    def announce_list_item(self):
        if not self.objects: return
        label = self.objects[self.list_selection_index].get("label", self._("Unnamed Object"))
        speak_message(f"{label}, {self.list_selection_index + 1} of {len(self.objects)}", interrupt=True)

    def jump_to_selected_object(self):
        if not self.objects: return
        
        selected_object = self.objects[self.list_selection_index]
        coords = selected_object.get("spatial_info", {}).get("start_coord")
        
        if coords:
            self.user_pos = list(coords) # Make a copy
            speak_message(self._("Jumping to %s.") % selected_object.get("label"), interrupt=True)
            self.exit_list_mode()
        else:
            speak_message(self._("Could not jump to this object as it has no coordinates."), interrupt=True)

    def read_overall_description(self):
        speak_message(self.overall_description, interrupt=True)

    def list_all_objects(self):
        if not self.objects:
            speak_message(self._("There are no objects in this scene."), interrupt=True)
            return
        
        labels = [item.get("label", self._("unlabeled object")) for item in self.objects]
        list_announcement = self._("Objects in this scene: %s") % ", ".join(labels)
        speak_message(list_announcement, interrupt=True)

    def announce_position(self):
        pos_announcement = f"{self.user_pos[0]}, {self.user_pos[1]}"
        
        object_at_pos = None
        for item in self.objects:
            coords = item.get("spatial_info", {}).get("start_coord")
            if coords and coords[0] == self.user_pos[0] and coords[1] == self.user_pos[1]:
                object_at_pos = item.get("label", self._("an object"))
                break

        if object_at_pos:
            full_announcement = f"{pos_announcement}, {object_at_pos}"
        else:
            full_announcement = pos_announcement

        speak_message(full_announcement, interrupt=True)

    def inspect_object(self):
        closest_item = None
        min_dist = float('inf')

        for item in self.objects:
            coords = item.get("spatial_info", {}).get("start_coord", None)
            if not coords: continue
            
            dist = math.sqrt((coords[0] - self.user_pos[0])**2 + (coords[1] - self.user_pos[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_item = item
        
        if closest_item and min_dist < 2.0:
            label = closest_item.get("label", self._("Unknown Object"))
            action_desc = closest_item.get("action_description", "")
            detailed_desc = closest_item.get("detailed_description", self._("No further details available."))
            
            full_description = f"{label}. {action_desc} {detailed_desc}"
            speak_message(full_description, interrupt=True)
        else:
            speak_message(self._("Nothing to inspect here."), interrupt=True)

    def draw(self):
        self.screen.fill((20, 20, 40))
        
        cell_width = self.screen.get_width() / self.grid_size[0]
        cell_height = self.screen.get_height() / self.grid_size[1]

        # Draw objects and highlight the selected one in list mode
        for i, item in enumerate(self.objects):
            coords = item.get("spatial_info", {}).get("start_coord")
            if coords:
                px = int(coords[0] * cell_width + cell_width / 2)
                py = int(coords[1] * cell_height + cell_height / 2)
                color = (100, 200, 100)
                if self.mode == "list" and i == self.list_selection_index:
                    color = (255, 255, 0) # Highlight yellow
                pygame.draw.circle(self.screen, color, (px, py), 10)

        user_px = int(self.user_pos[0] * cell_width + cell_width / 2)
        user_py = int(self.user_pos[1] * cell_height + cell_height / 2)
        pygame.draw.circle(self.screen, (255, 200, 200), (user_px, user_py), 8)

        pygame.display.flip()