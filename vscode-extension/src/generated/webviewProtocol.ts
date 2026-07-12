// Generated file. Do not edit manually.
// Source: contracts/webview-protocol.schema.json
// Generator: webview

export interface InboundMessage {
    direction: "inbound";
    action: "ppi/analysisComplete" | "ppi/error" | "ppi/progress";
    payload: string;
    messageId: string;
}

export interface OutboundMessage {
    direction: "outbound";
    command: "ppi/startAnalysis" | "ppi/cancelAnalysis" | "ppi/openDashboard";
    payload: string;
    messageId: string;
}

export type WebviewMessage =
    InboundMessage
    | OutboundMessage;
