<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Badge } from "$lib/components/ui/badge";
  import { ScrollArea } from "$lib/components/ui/scroll-area";
  import { createApiStore, makeApiCall, tauriApi } from "$lib/tauri-api";
  import type { ApiConfig } from "$lib/utils";

  let apiResponse = $state("");
  let fibNumber = $state(10);
  let fibResult = $state("");
  let streamData = $state<string[]>([]);
  let isStreaming = $state(false);
  let isCalculating = $state(false);

  // Create API store for reactive port discovery
  const apiStore = createApiStore();
  let apiConfig = $state<ApiConfig>({
    baseUrl: "http://127.0.0.1:8008",
    port: 8008,
    available: false,
  });

  // Subscribe to API config changes
  apiStore.subscribe((config) => {
    apiConfig = config;
  });

  async function testConnection() {
    try {
      const data = await makeApiCall("/v1/connect");
      apiResponse = JSON.stringify(data, null, 2);
    } catch (error) {
      apiResponse = `Connection failed: ${error}`;
    }
  }

  function calculateFibonacci() {
    if (isCalculating) return;

    isCalculating = true;
    fibResult = "Calculating...";

    setTimeout(async () => {
      try {
        const data = await makeApiCall("/v1/fibonacci", {
          method: "POST",
          body: JSON.stringify({ number: fibNumber }),
        });
        fibResult = JSON.stringify(data, null, 2);
      } catch (error) {
        fibResult = `Fibonacci calculation failed: ${error}`;
      } finally {
        isCalculating = false;
      }
    }, 0);
  }

  function startStreaming() {
    if (isStreaming) return;

    isStreaming = true;
    streamData = [];

    setTimeout(async () => {
      try {
        const response = await fetch(`${apiConfig.baseUrl}/v1/stream`);
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          while (isStreaming) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split("\n").filter((line) => line.trim());

            for (const line of lines) {
              try {
                const data = JSON.parse(line);
                streamData = [
                  ...streamData,
                  `Item ${data.count}: ${data.message}`,
                ];
              } catch {}
            }
          }
        }
      } catch (error) {
        streamData = [...streamData, `Streaming error: ${error}`];
      } finally {
        isStreaming = false;
      }
    }, 0);
  }

  function stopStreaming() {
    isStreaming = false;
  }

  function refreshApiDiscovery() {
    apiStore.refresh();
  }

  async function restartSidecar() {
    try {
      await tauriApi.restartSidecar();
      // Refresh API discovery after restart
      setTimeout(() => {
        apiStore.refresh();
      }, 2000);
    } catch (error) {
      console.error("Failed to restart sidecar:", error);
    }
  }
</script>

<div class="min-h-screen w-full bg-background p-6">
  <div class="mx-auto max-w-7xl space-y-8">
    <div class="text-center">
      <h1 class="text-4xl font-bold tracking-tight">Data Analyzer Pro</h1>
      <p class="text-lg text-muted-foreground mt-2">
        Test your Python FastAPI backend with dynamic port discovery
      </p>

      <!-- API Status Indicator -->
      <div class="flex items-center justify-center gap-4 mt-4">
        <div class="flex items-center gap-2">
          <Badge variant={apiConfig.available ? "default" : "destructive"}>
            {apiConfig.available ? "API Connected" : "API Disconnected"}
          </Badge>
          {#if apiConfig.available}
            <span class="text-sm text-muted-foreground"
              >Port: {apiConfig.port}</span
            >
          {/if}
        </div>
        <Button variant="outline" size="sm" onclick={refreshApiDiscovery}>
          Refresh Discovery
        </Button>
        <Button variant="outline" size="sm" onclick={restartSidecar}>
          Restart Sidecar
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Connection Test</CardTitle>
          <CardDescription>
            Test the basic connection to your Python backend with auto-discovery
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="text-sm text-muted-foreground mb-2">
            Current API: {apiConfig.baseUrl}
          </div>
          <Button
            onclick={testConnection}
            class="w-full"
            disabled={!apiConfig.available}
          >
            Test /v1/connect
          </Button>
          {#if apiResponse}
            <ScrollArea class="h-40 w-full rounded-md border p-4">
              <pre class="text-sm">{apiResponse}</pre>
            </ScrollArea>
          {/if}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fibonacci Calculator</CardTitle>
          <CardDescription>
            Calculate fibonacci numbers using the backend with dynamic port
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="fibInput">Number (0-10)</Label>
            <Input
              id="fibInput"
              type="number"
              bind:value={fibNumber}
              min="0"
              max="10"
            />
          </div>
          <Button
            onclick={calculateFibonacci}
            class="w-full"
            disabled={fibNumber < 0 ||
              fibNumber > 10 ||
              isCalculating ||
              !apiConfig.available}
          >
            {isCalculating ? "Calculating..." : "Calculate Fibonacci"}
          </Button>
          {#if fibResult}
            <ScrollArea class="h-40 w-full rounded-md border p-4">
              <pre class="text-sm">{fibResult}</pre>
            </ScrollArea>
          {/if}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Streaming Data</CardTitle>
          <CardDescription>
            Test real-time data streaming with auto-discovered port
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex gap-2">
            <Button
              onclick={startStreaming}
              disabled={isStreaming || !apiConfig.available}
              class="flex-1"
            >
              {isStreaming ? "Streaming..." : "Start Stream"}
            </Button>
            <Button
              variant="outline"
              onclick={stopStreaming}
              disabled={!isStreaming}
              class="flex-1"
            >
              Stop Stream
            </Button>
          </div>

          {#if isStreaming}
            <Badge variant="secondary">Streaming active</Badge>
          {/if}

          {#if streamData.length > 0}
            <ScrollArea class="h-48 w-full rounded-md border p-4">
              <div class="space-y-2">
                {#each streamData as item}
                  <div class="text-sm p-2 bg-secondary rounded">{item}</div>
                {/each}
              </div>
            </ScrollArea>
          {/if}
        </CardContent>
      </Card>
    </div>

    <!-- Port Discovery Info Card -->
    <Card>
      <CardHeader>
        <CardTitle>Dynamic Port Discovery</CardTitle>
        <CardDescription>
          Information about the automatic port discovery system
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="space-y-2">
            <Label>Discovery Status</Label>
            <Badge variant={apiConfig.available ? "default" : "secondary"}>
              {apiConfig.available ? "Active" : "Searching..."}
            </Badge>
          </div>
          <div class="space-y-2">
            <Label>Current Port</Label>
            <div class="text-sm font-mono bg-secondary p-2 rounded">
              {apiConfig.port}
            </div>
          </div>
          <div class="space-y-2">
            <Label>Base URL</Label>
            <div class="text-sm font-mono bg-secondary p-2 rounded">
              {apiConfig.baseUrl}
            </div>
          </div>
        </div>
        <div class="text-sm text-muted-foreground">
          <p>
            🚀 The system automatically discovers available ports in the range
            8008-8020.<br />
            🔄 If port 8008 is busy, it will find the next available port.<br />
            💾 Discovered configurations are cached for better performance.<br
            />
            🔗 All API calls automatically use the discovered port.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</div>
