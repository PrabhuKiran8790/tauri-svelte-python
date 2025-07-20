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

  let apiResponse = $state("");
  let fibNumber = $state(10);
  let fibResult = $state("");
  let streamData = $state<string[]>([]);
  let isStreaming = $state(false);
  let isCalculating = $state(false);

  async function testConnection() {
    try {
      const response = await fetch(`http://127.0.0.1:8008/v1/connect`);
      const data = await response.json();
      apiResponse = JSON.stringify(data, null, 2);
    } catch (error) {
      apiResponse = `Connection failed: ${error}`;
    }
  }

  function calculateFibonacci() {
    if (isCalculating) return;

    isCalculating = true;
    fibResult = "Calculating...";

    // Use setTimeout to ensure this runs in a separate task queue
    setTimeout(async () => {
      try {
        const response = await fetch("http://127.0.0.1:8008/v1/fibonacci", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ number: fibNumber }),
        });
        const data = await response.json();
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

    // Use setTimeout to ensure this runs in a separate task queue
    setTimeout(async () => {
      try {
        const response = await fetch("http://127.0.0.1:8008/v1/stream");
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
</script>

<div class="min-h-screen w-full bg-background p-6">
  <div class="mx-auto max-w-7xl space-y-8">
    <div class="text-center">
      <h1 class="text-4xl font-bold tracking-tight">Backend API Testing</h1>
      <p class="text-lg text-muted-foreground mt-2">
        Test your Python FastAPI backend endpoints
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Connection Test</CardTitle>
          <CardDescription
            >Test the basic connection to your Python backend</CardDescription
          >
        </CardHeader>
        <CardContent class="space-y-4">
          <Button onclick={testConnection} class="w-full">
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
          <CardDescription
            >Calculate fibonacci numbers using the backend</CardDescription
          >
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
            disabled={fibNumber < 0 || fibNumber > 10 || isCalculating}
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
          <CardDescription
            >Test real-time data streaming from the backend</CardDescription
          >
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex gap-2">
            <Button
              onclick={startStreaming}
              disabled={isStreaming}
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
  </div>
</div>
