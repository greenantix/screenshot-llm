#!/usr/bin/env python3
"""
GTK Settings Window - Phase 3 of Tkinter to GTK Migration

Provides a user-friendly dialog for configuring the application.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import json
import os
from typing import Dict, Any

class SettingsWindow(Gtk.Dialog):
    """
    A GTK dialog for managing application settings.
    """

    def __init__(self, parent, config: Dict[str, Any]):
        super().__init__(title="Settings", transient_for=parent, flags=0)
        self.config = config

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        self.set_default_size(500, 400)
        self.get_content_area().set_spacing(10)

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Create the settings UI components."""
        notebook = Gtk.Notebook()
        self.get_content_area().add(notebook)

        # LLM Settings Tab
        llm_page = self._create_llm_settings_page()
        notebook.append_page(llm_page, Gtk.Label(label="LLM"))

        # Advanced Settings Tab
        advanced_page = self._create_advanced_settings_page()
        notebook.append_page(advanced_page, Gtk.Label(label="Advanced"))

    def _create_llm_settings_page(self) -> Gtk.Box:
        """Create the UI for LLM settings."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page.set_border_width(10)

        # LLM Provider
        provider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        provider_label = Gtk.Label(label="Provider:")
        self.provider_combo = Gtk.ComboBoxText()
        self.provider_combo.append_text("openai")
        self.provider_combo.append_text("anthropic")
        provider_box.pack_start(provider_label, False, False, 0)
        provider_box.pack_start(self.provider_combo, True, True, 0)
        page.pack_start(provider_box, False, False, 0)

        # API Key
        api_key_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        api_key_label = Gtk.Label(label="API Key:")
        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_visibility(False)
        api_key_box.pack_start(api_key_label, False, False, 0)
        api_key_box.pack_start(self.api_key_entry, True, True, 0)
        page.pack_start(api_key_box, False, False, 0)

        # Model
        model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        model_label = Gtk.Label(label="Model:")
        self.model_entry = Gtk.Entry()
        model_box.pack_start(model_label, False, False, 0)
        model_box.pack_start(self.model_entry, True, True, 0)
        page.pack_start(model_box, False, False, 0)
        
        # Quick Prompt (for pop-up)
        quick_prompt_label = Gtk.Label(label="Quick Prompt (for pop-up):")
        quick_prompt_label.set_halign(Gtk.Align.START)
        page.pack_start(quick_prompt_label, False, False, 0)
        
        quick_scroll = Gtk.ScrolledWindow()
        quick_scroll.set_size_request(-1, 80)
        quick_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.quick_prompt_view = Gtk.TextView()
        self.quick_prompt_view.set_wrap_mode(Gtk.WrapMode.WORD)
        quick_scroll.add(self.quick_prompt_view)
        page.pack_start(quick_scroll, False, False, 0)
        
        # Detailed Prompt (for main chat)
        detailed_prompt_label = Gtk.Label(label="Detailed Prompt (for main chat):")
        detailed_prompt_label.set_halign(Gtk.Align.START)
        page.pack_start(detailed_prompt_label, False, False, 0)
        
        detailed_scroll = Gtk.ScrolledWindow()
        detailed_scroll.set_size_request(-1, 80)
        detailed_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.detailed_prompt_view = Gtk.TextView()
        self.detailed_prompt_view.set_wrap_mode(Gtk.WrapMode.WORD)
        detailed_scroll.add(self.detailed_prompt_view)
        page.pack_start(detailed_scroll, False, False, 0)

        return page

    def _create_advanced_settings_page(self) -> Gtk.Box:
        """Create the UI for advanced settings."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page.set_border_width(10)

        # Mouse Device Path
        mouse_device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mouse_device_label = Gtk.Label(label="Mouse Device Path:")
        self.mouse_device_entry = Gtk.Entry()
        mouse_device_box.pack_start(mouse_device_label, False, False, 0)
        mouse_device_box.pack_start(self.mouse_device_entry, True, True, 0)
        page.pack_start(mouse_device_box, False, False, 0)

        return page

    def _load_settings(self):
        """Load current settings into the UI."""
        # LLM settings
        llm_config = self.config.get("llm", {})
        self.provider_combo.set_active_id(llm_config.get("provider", "openai"))
        self.api_key_entry.set_text(llm_config.get("api_key", ""))
        self.model_entry.set_text(llm_config.get("model", ""))
        
        # Load prompts with defaults
        quick_prompt = llm_config.get("quick_prompt", 
            "You are an expert developer's assistant. Analyze the screenshot and provide a concise, one-paragraph summary or a single, most-likely command. Use markdown.")
        detailed_prompt = llm_config.get("detailed_prompt",
            "You are an expert developer's assistant. Analyze the screenshot in detail and provide helpful insights, explanations, and actionable suggestions. Use markdown formatting.")
        
        self.quick_prompt_view.get_buffer().set_text(quick_prompt)
        self.detailed_prompt_view.get_buffer().set_text(detailed_prompt)

        # Advanced settings
        advanced_config = self.config.get("advanced", {})
        self.mouse_device_entry.set_text(advanced_config.get("mouse_device_path", ""))

    def save_settings(self) -> Dict[str, Any]:
        """Save the settings from the UI."""
        # Ensure config dictionaries exist
        if "llm" not in self.config:
            self.config["llm"] = {}
        if "advanced" not in self.config:
            self.config["advanced"] = {}
            
        # LLM settings
        self.config["llm"]["provider"] = self.provider_combo.get_active_text()
        self.config["llm"]["api_key"] = self.api_key_entry.get_text()
        self.config["llm"]["model"] = self.model_entry.get_text()
        
        # Save prompts
        quick_buffer = self.quick_prompt_view.get_buffer()
        quick_text = quick_buffer.get_text(quick_buffer.get_start_iter(), quick_buffer.get_end_iter(), False)
        self.config["llm"]["quick_prompt"] = quick_text
        
        detailed_buffer = self.detailed_prompt_view.get_buffer()
        detailed_text = detailed_buffer.get_text(detailed_buffer.get_start_iter(), detailed_buffer.get_end_iter(), False)
        self.config["llm"]["detailed_prompt"] = detailed_text

        # Advanced settings
        self.config["advanced"]["mouse_device_path"] = self.mouse_device_entry.get_text()

        return self.config