import React, { useEffect, useRef, useState } from "react";

const ServerLog: React.FC<{ serverLog: string }> = ({ serverLog }) => {
    const preRef = useRef<HTMLPreElement>(null);
    const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);

    // 监听滚动，判断用户是否上翻
    useEffect(() => {
        const pre = preRef.current;
        if (!pre) return;
        const handleScroll = () => {
            // 判断是否在底部（允许 2px 误差）
            const atBottom = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 2;
            setIsUserScrolledUp(!atBottom);
        };
        pre.addEventListener("scroll", handleScroll);
        return () => pre.removeEventListener("scroll", handleScroll);
    }, []);

    // serverLog 变化时自动滚动到底部（如果没上翻）
    useEffect(() => {
        const pre = preRef.current;
        if (pre && !isUserScrolledUp) {
            pre.scrollTop = pre.scrollHeight;
        }
    }, [serverLog, isUserScrolledUp]);

    return (
        <pre
            ref={preRef}
            style={{
                whiteSpace: "pre-wrap",
                margin: 0,
                maxHeight: "500px",
                overflow: "auto",
            }}
        >
            {serverLog}
        </pre>
    );
};

export default ServerLog;
