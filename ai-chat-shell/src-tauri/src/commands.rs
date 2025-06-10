#[tauri::command]
pub async fn inject_theme(_window: tauri::Window, theme: String) -> Result<(), String> {
    let css = if theme == "dark" {
        r#"
        :root {
            color-scheme: dark;
        }
        body {
            background-color: #1a1a1a !important;
        }
        "#
    } else {
        r#"
        :root {
            color-scheme: light;
        }
        "#
    };
    
    // This would inject CSS into the webview if possible
    // Implementation depends on the specific webview capabilities
    // For now, this is a placeholder for future webview theming
    println!("Theme injection request: {}", theme);
    println!("CSS to inject: {}", css);
    
    Ok(())
}

#[tauri::command]
pub async fn get_app_config_dir() -> Result<String, String> {
    match tauri::api::path::app_config_dir(&tauri::Config::default()) {
        Some(path) => Ok(path.to_string_lossy().to_string()),
        None => Err("Could not determine app config directory".to_string()),
    }
}