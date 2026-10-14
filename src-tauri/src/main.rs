#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::Write, path::PathBuf, process::{Command, Stdio}, sync::Mutex};
use tauri::{Manager, State};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

#[derive(Default, Clone, Serialize, Deserialize)]
struct Settings { repo: Option<PathBuf>, vexcom: Option<PathBuf>, sd: Option<PathBuf> }
struct AppState { settings: Mutex<Settings>, data: PathBuf, busy: Mutex<()> }

fn local(window: &tauri::Window) -> Result<(), String> {
    if window.label() != "main" { return Err("Untrusted window".into()); }
    let webview=window.app_handle().get_webview_window("main").ok_or("Missing local webview")?;
    let url=webview.url().map_err(|e|e.to_string())?;
    let packaged=url.scheme()=="tauri" && url.host_str()==Some("localhost") || url.scheme()=="http" && url.host_str()==Some("tauri.localhost");
    let development=cfg!(debug_assertions) && url.scheme()=="http" && matches!(url.host_str(),Some("localhost")|Some("127.0.0.1")) && url.port()==Some(5173);
    if !packaged && !development { return Err("Native commands are restricted to the bundled local application".into()); } Ok(())
}
#[tauri::command]
fn settings(window: tauri::Window, state: State<AppState>) -> Result<Settings,String> {
    local(&window)?; Ok(state.settings.lock().map_err(|e|e.to_string())?.clone())
}
#[tauri::command]
async fn choose(window: tauri::Window, state: State<'_,AppState>, kind: String) -> Result<Settings,String> {
    local(&window)?;
    let path = if kind == "vexcom" { rfd::AsyncFileDialog::new().set_title("Select your installed VEX vexcom utility").pick_file().await }
        else if kind == "repo" || kind == "sd" { rfd::AsyncFileDialog::new().set_title(if kind=="repo" {"Choose robot repository (or empty folder to clone into)"} else {"Choose mounted SD card folder"}).pick_folder().await }
        else { return Err("Unknown selection".into()); };
    let mut saved = state.settings.lock().map_err(|e|e.to_string())?;
    if let Some(path)=path { let path=path.path().to_path_buf(); match kind.as_str() {"repo"=>saved.repo=Some(path),"sd"=>saved.sd=Some(path),_=>saved.vexcom=Some(path)};
        std::fs::write(state.data.join("settings.json"), serde_json::to_vec(&*saved).unwrap()).map_err(|e|e.to_string())?;
    } Ok(saved.clone())
}
#[tauri::command]
async fn service(window: tauri::Window, state: State<'_,AppState>, action: String, mut args: Value) -> Result<Value,String> {
    local(&window)?;
    let saved=state.settings.lock().map_err(|e|e.to_string())?.clone();
    let data=state.data.clone();
    let app=window.app_handle().clone();
    // Native work runs off the UI thread. No shell plugin or arbitrary command is exposed.
    tauri::async_runtime::spawn_blocking(move || {
        let state=app.state::<AppState>();
        let _guard=state.busy.lock().map_err(|e|e.to_string())?;
        if !args.is_object() { args=json!({}); }
        args["_root"]=json!(saved.repo); args["_tool"]=json!(saved.vexcom);
        args["_sd"]=json!(saved.sd); args["_data"]=json!(data);
        let mut command;
        if cfg!(debug_assertions) {
            command=Command::new(std::env::var("CC_BACKEND_PYTHON").unwrap_or_else(|_| if cfg!(windows) {"python".into()} else {"python3".into()}));
            command.arg(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../service/main.py"));
        } else {
            let exe=std::env::current_exe().map_err(|e|e.to_string())?;
            command=Command::new(exe.parent().ok_or("Missing application directory")?.join(if cfg!(windows) {"cc-service.exe"} else {"cc-service"}));
        }
        #[cfg(windows)] { use std::os::windows::process::CommandExt; command.creation_flags(0x08000000); }
        let mut child=command.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().map_err(|e|format!("Local service unavailable: {e}"))?;
        child.stdin.take().unwrap().write_all(json!({"action":action,"args":args}).to_string().as_bytes()).map_err(|e|e.to_string())?;
        let output=child.wait_with_output().map_err(|e|e.to_string())?;
        let response:Value=serde_json::from_slice(&output.stdout).map_err(|_|"Local service returned an invalid response".to_string())?;
        if response["ok"]==true { Ok(response["result"].clone()) } else { Err(response["error"].as_str().unwrap_or("Local service failed").to_string()) }
    }).await.map_err(|e|e.to_string())?
}
fn main() {
    tauri::Builder::default().setup(|app| {
        let data=app.path().app_data_dir()?; std::fs::create_dir_all(&data)?;
        let settings=std::fs::read(data.join("settings.json")).ok().and_then(|b|serde_json::from_slice(&b).ok()).unwrap_or_default();
        app.manage(AppState { settings:Mutex::new(settings), data, busy:Mutex::new(()) }); Ok(())
    }).invoke_handler(tauri::generate_handler![settings,choose,service]).run(tauri::generate_context!()).expect("Could not start Control Center");
}
