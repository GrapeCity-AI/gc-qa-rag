import React from "react";

const ServerLog: React.FC<{ serverLog: string }> = ({ serverLog }) => (
    <pre
        style={{
            whiteSpace: "pre-wrap",
            color: "#0f0",
            background: "transparent",
            margin: 0,
        }}
    >
        {serverLog}
    </pre>
);

export default ServerLog; 