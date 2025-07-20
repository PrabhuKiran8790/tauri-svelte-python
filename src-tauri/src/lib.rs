use std::sync::{Arc, Mutex};
use tauri::{Emitter, Manager, RunEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

// Wrapper struct for sidecar process with automatic cleanup
struct SidecarProcess {
    process: Option<CommandChild>,
}

impl SidecarProcess {
    fn new() -> Self {
        Self { process: None }
    }
    
    fn set_process(&mut self, process: CommandChild) {
        self.process = Some(process);
    }
    
    fn take_process(&mut self) -> Option<CommandChild> {
        self.process.take()
    }
    
    fn has_process(&self) -> bool {
        self.process.is_some()
    }
}

impl Drop for SidecarProcess {
    fn drop(&mut self) {
        if let Some(process) = self.process.take() {
            println!("[tauri] SidecarProcess dropping, killing process...");
            let _ = process.kill();
        }
    }
}

// Helper function to cleanup sidecar process
fn cleanup_sidecar_process(app_handle: &tauri::AppHandle) {
    println!("[tauri] Cleaning up sidecar process...");
    if let Some(child_process) = app_handle.try_state::<Arc<Mutex<SidecarProcess>>>() {
        if let Ok(mut child) = child_process.lock() {
            if let Some(mut process) = child.take_process() {
                // First, try graceful shutdown via stdin
                let command = "sidecar shutdown\n";
                let buf: &[u8] = command.as_bytes();
                if let Err(e) = process.write(buf) {
                    println!("[tauri] Failed to send shutdown command: {}", e);
                } else {
                    println!("[tauri] Sent graceful shutdown command to sidecar.");
                    // Wait a shorter time for graceful shutdown in production
                    std::thread::sleep(std::time::Duration::from_millis(500));
                }

                // Force kill the process - this is crucial for production builds
                match process.kill() {
                    Ok(_) => {
                        println!("[tauri] Sidecar process terminated successfully.");
                        // Wait a bit to ensure the process is fully cleaned up
                        std::thread::sleep(std::time::Duration::from_millis(200));
                    },
                    Err(e) => println!("[tauri] Failed to kill sidecar process (may already be dead): {}", e),
                }
            } else {
                println!("[tauri] No sidecar process found to cleanup.");
            }
        } else {
            println!("[tauri] Failed to acquire lock on sidecar process state.");
        }
    } else {
        println!("[tauri] Sidecar process state not found.");
    }
    
    // Additional cleanup: try to kill any processes on the sidecar ports
    // This is a fallback for production builds where the process might not be tracked properly
    println!("[tauri] Performing additional port cleanup...");
    cleanup_sidecar_ports();
}

// Additional cleanup function to kill processes on sidecar ports
fn cleanup_sidecar_ports() {
    use std::process::Command;
    
    let ports = [8008, 8009, 8010, 8011, 8012];
    
    for port in ports {
        // Try to find and kill processes on each port
        if let Ok(output) = Command::new("lsof")
            .args(["-ti", &format!(":{}", port)])
            .output()
        {
            let pids_str = String::from_utf8_lossy(&output.stdout);
            let pids: Vec<&str> = pids_str.trim().split('\n').filter(|s| !s.is_empty()).collect();
            
            for pid in pids {
                if let Ok(pid_num) = pid.parse::<u32>() {
                    println!("[tauri] Killing process {} on port {}", pid_num, port);
                    let _ = Command::new("kill")
                        .args(["-9", &pid_num.to_string()])
                        .output();
                }
            }
        }
    }
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn toggle_fullscreen(window: tauri::Window) {
    if let Ok(is_fullscreen) = window.is_fullscreen() {
        window.set_fullscreen(!is_fullscreen).unwrap();
    }
}

// Helper function to spawn the sidecar and monitor its stdout/stderr
fn spawn_and_monitor_sidecar(app_handle: tauri::AppHandle) -> Result<(), String> {
    // Check if a sidecar process already exists
    if let Some(state) = app_handle.try_state::<Arc<Mutex<SidecarProcess>>>() {
        let child_process = state.lock().unwrap();
        if child_process.has_process() {
            // A sidecar is already running, do not spawn a new one
            println!("[tauri] Sidecar is already running. Skipping spawn.");
            return Ok(()); // Exit early since sidecar is already running
        }
    }
    // Spawn sidecar
    let sidecar_command = app_handle
        .shell()
        .sidecar("main")
        .map_err(|e| e.to_string())?;
    let (mut rx, child) = sidecar_command.spawn().map_err(|e| e.to_string())?;
    // Store the child process in the app state
    if let Some(state) = app_handle.try_state::<Arc<Mutex<SidecarProcess>>>() {
        state.lock().unwrap().set_process(child);
    } else {
        return Err("Failed to access app state".to_string());
    }

    // Spawn an async task to handle sidecar communication
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    println!("Sidecar stdout: {}", line);
                    // Emit the line to the frontend
                    app_handle
                        .emit("sidecar-stdout", line.to_string())
                        .expect("Failed to emit sidecar stdout event");
                }
                CommandEvent::Stderr(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    eprintln!("Sidecar stderr: {}", line);
                    // Emit the error line to the frontend
                    app_handle
                        .emit("sidecar-stderr", line.to_string())
                        .expect("Failed to emit sidecar stderr event");
                }
                _ => {}
            }
        }
    });

    Ok(())
}

// Define a command to shutdown sidecar process
#[tauri::command]
fn shutdown_sidecar(app_handle: tauri::AppHandle) -> Result<String, String> {
    println!("[tauri] Received command to shutdown sidecar.");
    // Access the sidecar process state
    if let Some(state) = app_handle.try_state::<Arc<Mutex<SidecarProcess>>>() {
        let mut child_process = state
            .lock()
            .map_err(|_| "[tauri] Failed to acquire lock on sidecar process.")?;

        if let Some(mut process) = child_process.take_process() {
            let command = "sidecar shutdown\n"; // Add newline to signal the end of the command

            // Attempt to write the command to the sidecar's stdin for graceful shutdown
            if let Err(err) = process.write(command.as_bytes()) {
                println!("[tauri] Failed to write to sidecar stdin: {}, attempting force kill", err);
                // If stdin write fails, try to kill the process directly
                match process.kill() {
                    Ok(_) => {
                        println!("[tauri] Sidecar process forcefully terminated.");
                        return Ok("Sidecar forcefully terminated.".to_string());
                    }
                    Err(kill_err) => {
                        println!("[tauri] Failed to kill sidecar process: {}", kill_err);
                        return Err(format!("Failed to shutdown sidecar: stdin write failed ({}), kill failed ({})", err, kill_err));
                    }
                }
            }

            println!("[tauri] Sent 'sidecar shutdown' command to sidecar.");
            
            // Wait a moment and then force kill if still running
            std::thread::sleep(std::time::Duration::from_millis(500));
            match process.kill() {
                Ok(_) => println!("[tauri] Sidecar process terminated."),
                Err(_) => println!("[tauri] Sidecar process already terminated or not found."),
            }
            
            Ok("Sidecar shutdown completed.".to_string())
        } else {
            println!("[tauri] No active sidecar process to shutdown.");
            Err("No active sidecar process to shutdown.".to_string())
        }
    } else {
        Err("Sidecar process state not found.".to_string())
    }
}

// Define a command to start sidecar process.
#[tauri::command]
fn start_sidecar(app_handle: tauri::AppHandle) -> Result<String, String> {
    println!("[tauri] Received command to start sidecar.");
    spawn_and_monitor_sidecar(app_handle)?;
    Ok("Sidecar spawned and monitoring started.".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Add any necessary plugins
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            // Store the initial sidecar process in the app state with automatic cleanup
            app.manage(Arc::new(Mutex::new(SidecarProcess::new())));
            
            // Set up window close event handler for all windows
            let app_handle = app.handle().clone();
            if let Some(window) = app.get_webview_window("main") {
                window.on_window_event(move |event| {
                    match event {
                        tauri::WindowEvent::CloseRequested { .. } => {
                            println!("[tauri] Window close requested, cleaning up sidecar...");
                            cleanup_sidecar_process(&app_handle);
                        }
                        tauri::WindowEvent::Destroyed => {
                            println!("[tauri] Window destroyed, cleaning up sidecar...");
                            cleanup_sidecar_process(&app_handle);
                        }
                        _ => {}
                    }
                });
            }
            
            // Clone the app handle for use elsewhere
            let app_handle = app.handle().clone();
            // Spawn the Python sidecar on startup
            println!("[tauri] Creating sidecar...");
            spawn_and_monitor_sidecar(app_handle).ok();
            println!("[tauri] Sidecar spawned and monitoring started.");
            Ok(())
        })
        // Register the shutdown_server command
        .invoke_handler(tauri::generate_handler![
            greet,
            start_sidecar,
            shutdown_sidecar,
            toggle_fullscreen
        ])
        .build(tauri::generate_context!())
        .expect("Error while running tauri application")
        .run(|app_handle, event| match event {
            // Ensure the Python sidecar is killed when the app is closed
            RunEvent::ExitRequested { .. } => {
                println!("[tauri] Application exit requested, cleaning up sidecar...");
                cleanup_sidecar_process(&app_handle);
            }
            RunEvent::Exit => {
                println!("[tauri] Application exiting, final cleanup...");
                cleanup_sidecar_process(&app_handle);
            }
            _ => {}
        });
}

