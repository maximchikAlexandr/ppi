import { MantineProvider } from "@mantine/core";
import React from "react";
import ReactDOM from "react-dom/client";

import "@mantine/core/styles.css";
import "@mantine/charts/styles.css";
import "./app.css";

import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MantineProvider
      defaultColorScheme="light"
      theme={{
        primaryColor: "teal",
        defaultRadius: "md",
        fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        headings: { fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif" },
      }}
    >
      <App />
    </MantineProvider>
  </React.StrictMode>,
);
