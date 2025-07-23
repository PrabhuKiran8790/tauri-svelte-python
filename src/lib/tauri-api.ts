import { invoke } from "@tauri-apps/api/core";
import { Command } from "@tauri-apps/plugin-shell";
import { listen } from "@tauri-apps/api/event";
import {
  apiClient,
  parsePortInfo,
  type PortInfo,
  type ApiConfig,
} from "./utils";

export class TauriApiIntegration {
  private portDiscovered = false;
  private sidecarStdoutListener: (() => void) | null = null;

  constructor() {
    this.initializeSidecarMonitoring();
  }

  private async initializeSidecarMonitoring() {
    try {
      // In Tauri environment, we can monitor sidecar output
      if (typeof window !== "undefined" && "invoke" in window) {
        console.log("[Tauri API] Initializing sidecar monitoring...");
        await this.monitorSidecarOutput();
      }
    } catch (error) {
      console.warn(
        "[Tauri API] Failed to initialize sidecar monitoring:",
        error
      );
    }
  }

  private async monitorSidecarOutput() {
    try {
      console.log("[Tauri API] Setting up sidecar output monitoring...");

      // Listen for sidecar stdout events from Rust backend
      this.sidecarStdoutListener = await listen(
        "sidecar-stdout",
        (event: any) => {
          const output = event.payload as string;
          console.log("[Tauri API] Sidecar stdout:", output);

          // Parse port info from sidecar output
          const portInfo = parsePortInfo(output);
          if (portInfo && !this.portDiscovered) {
            this.portDiscovered = true;
            console.log(
              `[Tauri API] Port discovered from sidecar: ${portInfo.port}`
            );

            // Update API client with discovered port
            (apiClient as any).updateConfig({
              baseUrl: portInfo.url,
              port: portInfo.port,
              available: true,
            });

            this.notifyPortDiscovered({
              baseUrl: portInfo.url,
              port: portInfo.port,
              available: true,
            });
          }
        }
      );

      // Also listen for stderr for debugging
      await listen("sidecar-stderr", (event: any) => {
        const output = event.payload as string;
        console.warn("[Tauri API] Sidecar stderr:", output);
      });

      // Fallback to port scanning if sidecar doesn't provide port info
      apiClient.onPortDiscovered((config: ApiConfig) => {
        if (!this.portDiscovered) {
          this.portDiscovered = true;
          console.log(
            `[Tauri API] Port discovered via scanning: ${config.port}`
          );
          this.notifyPortDiscovered(config);
        }
      });

      console.log("[Tauri API] Sidecar monitoring setup complete");
    } catch (error) {
      console.error("[Tauri API] Error setting up sidecar monitoring:", error);
      // Fallback to port scanning
      console.log("[Tauri API] Falling back to port scanning...");
    }
  }

  private notifyPortDiscovered(config: ApiConfig) {
    // Emit custom event for components to listen to
    if (typeof window !== "undefined") {
      const event = new CustomEvent("sidecar-port-discovered", {
        detail: config,
      });
      window.dispatchEvent(event);
    }
  }

  public async waitForSidecar(timeoutMs: number = 15000): Promise<ApiConfig> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Sidecar port discovery timeout"));
      }, timeoutMs);

      const handlePortDiscovered = (event: any) => {
        clearTimeout(timeout);
        window.removeEventListener(
          "sidecar-port-discovered",
          handlePortDiscovered
        );
        resolve(event.detail);
      };

      if (typeof window !== "undefined") {
        window.addEventListener(
          "sidecar-port-discovered",
          handlePortDiscovered
        );
      }

      // Check if port is already discovered
      const currentConfig = apiClient.getConfig();
      if (currentConfig.available) {
        clearTimeout(timeout);
        if (typeof window !== "undefined") {
          window.removeEventListener(
            "sidecar-port-discovered",
            handlePortDiscovered
          );
        }
        resolve(currentConfig);
      }
    });
  }

  public async invokeTauriCommand(command: string, args?: any): Promise<any> {
    try {
      return await invoke(command, args);
    } catch (error) {
      console.error(`[Tauri API] Failed to invoke command ${command}:`, error);
      throw error;
    }
  }

  public async startSidecar(): Promise<string> {
    try {
      const result = await invoke("start_sidecar");
      console.log("[Tauri API] Sidecar started:", result);
      return result as string;
    } catch (error) {
      console.error("[Tauri API] Failed to start sidecar:", error);
      throw error;
    }
  }

  public async shutdownSidecar(): Promise<string> {
    try {
      const result = await invoke("shutdown_sidecar");
      console.log("[Tauri API] Sidecar shutdown:", result);
      return result as string;
    } catch (error) {
      console.error("[Tauri API] Failed to shutdown sidecar:", error);
      throw error;
    }
  }

  public async restartSidecar(): Promise<string> {
    try {
      console.log("[Tauri API] Restarting sidecar...");
      await this.shutdownSidecar();
      // Wait a moment before restarting
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const result = await this.startSidecar();
      // Reset port discovery state
      this.portDiscovered = false;
      return result;
    } catch (error) {
      console.error("[Tauri API] Failed to restart sidecar:", error);
      throw error;
    }
  }

  public cleanup() {
    // Cleanup event listeners
    if (this.sidecarStdoutListener) {
      this.sidecarStdoutListener();
      this.sidecarStdoutListener = null;
    }
  }

  public getApiClient() {
    return apiClient;
  }
}

// Global Tauri API integration instance
export const tauriApi = new TauriApiIntegration();

// Utility hooks for Svelte components
export function createApiStore() {
  let config: ApiConfig = {
    baseUrl: "http://127.0.0.1:8008",
    port: 8008,
    available: false,
  };

  const subscribers = new Set<(config: ApiConfig) => void>();

  function subscribe(callback: (config: ApiConfig) => void) {
    subscribers.add(callback);

    // Immediately call with current config
    callback(config);

    return () => {
      subscribers.delete(callback);
    };
  }

  function update(newConfig: ApiConfig) {
    config = newConfig;
    subscribers.forEach((callback) => callback(config));
  }

  // Listen for port discovery
  apiClient.onPortDiscovered(update);

  return {
    subscribe,
    get: () => config,
    refresh: () => apiClient.refreshPortDiscovery(),
  };
}

// Helper function to make API calls with automatic port discovery
export async function makeApiCall(
  endpoint: string,
  options?: RequestInit
): Promise<any> {
  const config = apiClient.getConfig();

  if (!config.available) {
    // Try to discover port first
    await apiClient.refreshPortDiscovery();
    const updatedConfig = apiClient.getConfig();

    if (!updatedConfig.available) {
      throw new Error(
        "API server not available. Please ensure the sidecar is running."
      );
    }
  }

  const url = `${config.baseUrl}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}
