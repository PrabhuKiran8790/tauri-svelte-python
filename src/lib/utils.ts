import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Dynamic port discovery and API utilities
export interface PortInfo {
  type: "port_info";
  mode: "sidecar" | "standalone";
  port: number;
  url: string;
  docs_url: string;
  health_url: string;
}

export interface ApiConfig {
  baseUrl: string;
  port: number;
  available: boolean;
}

class ApiClient {
  private config: ApiConfig = {
    baseUrl: "http://127.0.0.1:8008",
    port: 8008,
    available: false,
  };

  private portDiscoveryListeners: ((config: ApiConfig) => void)[] = [];

  constructor() {
    this.detectSidecarPort();
  }

  private async detectSidecarPort() {
    // Try to detect port from various sources
    await Promise.race([
      this.detectFromTauriSidecar(),
      this.detectFromStandardPorts(),
      this.detectFromStoredConfig(),
    ]);
  }

  private async detectFromTauriSidecar(): Promise<void> {
    // In Tauri environment, we can listen for sidecar output
    if (typeof window !== "undefined" && "invoke" in window) {
      try {
        // This would be implemented with Tauri's sidecar monitoring
        // For now, we'll fall back to port scanning
        console.log(
          "[API Client] Tauri environment detected, attempting port discovery..."
        );
      } catch (error) {
        console.warn(
          "[API Client] Failed to detect port from Tauri sidecar:",
          error
        );
      }
    }
  }

  private async detectFromStandardPorts(): Promise<void> {
    const portRange = [
      8008, 8009, 8010, 8011, 8012, 8013, 8014, 8015, 8016, 8017, 8018, 8019,
      8020,
    ];

    for (const port of portRange) {
      try {
        const response = await fetch(`http://127.0.0.1:${port}/health`, {
          method: "GET",
          signal: AbortSignal.timeout(1000), // 1 second timeout
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === "healthy") {
            this.updateConfig({
              baseUrl: `http://127.0.0.1:${port}`,
              port,
              available: true,
            });
            console.log(`[API Client] Found API server on port ${port}`);
            return;
          }
        }
      } catch (error) {
        // Port not available or server not responding, continue
        continue;
      }
    }

    console.warn("[API Client] No API server found on standard ports");
  }

  private async detectFromStoredConfig(): Promise<void> {
    // Check if we have a stored configuration
    if (typeof localStorage !== "undefined") {
      const stored = localStorage.getItem("api_config");
      if (stored) {
        try {
          const config = JSON.parse(stored) as ApiConfig;
          // Verify the stored config is still valid
          const response = await fetch(`${config.baseUrl}/health`, {
            method: "GET",
            signal: AbortSignal.timeout(1000),
          });

          if (response.ok) {
            this.updateConfig(config);
            console.log(`[API Client] Using stored config: ${config.baseUrl}`);
            return;
          }
        } catch (error) {
          // Stored config is invalid, remove it
          localStorage.removeItem("api_config");
        }
      }
    }
  }

  public updateConfig(newConfig: ApiConfig) {
    this.config = { ...newConfig };

    // Store in localStorage for future use
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("api_config", JSON.stringify(this.config));
    }

    // Notify listeners
    this.portDiscoveryListeners.forEach((listener) => listener(this.config));
  }

  public onPortDiscovered(callback: (config: ApiConfig) => void) {
    this.portDiscoveryListeners.push(callback);

    // If port is already discovered, call immediately
    if (this.config.available) {
      callback(this.config);
    }
  }

  public getConfig(): ApiConfig {
    return { ...this.config };
  }

  public getBaseUrl(): string {
    return this.config.baseUrl;
  }

  public async get(endpoint: string): Promise<any> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(
        `API request failed: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  public async post(endpoint: string, data?: any): Promise<any> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new Error(
        `API request failed: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  public async refreshPortDiscovery(): Promise<void> {
    console.log("[API Client] Refreshing port discovery...");
    this.config.available = false;
    await this.detectSidecarPort();
  }
}

// Global API client instance
export const apiClient = new ApiClient();

// Utility function to wait for API to be available
export async function waitForApi(
  timeoutMs: number = 10000
): Promise<ApiConfig> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error("API discovery timeout"));
    }, timeoutMs);

    apiClient.onPortDiscovered((config) => {
      clearTimeout(timeout);
      resolve(config);
    });

    // If already available, resolve immediately
    const currentConfig = apiClient.getConfig();
    if (currentConfig.available) {
      clearTimeout(timeout);
      resolve(currentConfig);
    }
  });
}

// Parse port info from sidecar output
export function parsePortInfo(output: string): PortInfo | null {
  const portInfoMatch = output.match(/\[sidecar\] PORT_INFO: (.+)/);
  if (portInfoMatch) {
    try {
      return JSON.parse(portInfoMatch[1]) as PortInfo;
    } catch (error) {
      console.error("Failed to parse port info:", error);
    }
  }
  return null;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any }
  ? Omit<T, "children">
  : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & {
  ref?: U | null;
};
