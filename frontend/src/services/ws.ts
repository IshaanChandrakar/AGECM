// STOMP-over-WebSocket client for live dashboard updates.

import { Client, IMessage } from "@stomp/stompjs";

type Handler = (payload: any) => void;

export function connect(handlers: {
  telemetry?: Handler;
  alerts?: Handler;
  front?: Handler;
  onStatus?: (connected: boolean) => void;
}): Client {
  const url = `${location.origin.replace(/^http/, "ws")}/ws`;
  const client = new Client({
    brokerURL: url,
    reconnectDelay: 3000,
    onConnect: () => {
      handlers.onStatus?.(true);
      const sub = (topic: string, h?: Handler) =>
        h && client.subscribe(topic, (m: IMessage) => {
          try { h(JSON.parse(m.body)); } catch { /* ignore */ }
        });
      sub("/topic/telemetry", handlers.telemetry);
      sub("/topic/alerts", handlers.alerts);
      sub("/topic/front", handlers.front);
    },
    onWebSocketClose: () => handlers.onStatus?.(false),
  });
  client.activate();
  return client;
}
