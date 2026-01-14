import html2canvas from "html2canvas";

export async function captureDivToClipboard(
    div: HTMLDivElement,
    paddingV: number = 0,
    paddingH: number = 0,
): Promise<boolean> {
    try {
        // Check if the input is a valid div element
        if (!(div instanceof HTMLDivElement)) {
            throw new Error("Invalid input: The provided element is not a valid HTMLDivElement.");
        }

        // Get the original size and position of the div
        const rect = div.getBoundingClientRect();
        const width = rect.width + paddingH * 2; // Add horizontal padding
        const height = rect.height + paddingV * 2; // Add vertical padding

        // Create a temporary container to render the content with padding
        const tempDiv = document.createElement("div");
        tempDiv.style.position = "absolute";
        tempDiv.style.top = "-9999px"; // Move out of the visible area
        tempDiv.style.width = `${width}px`;
        tempDiv.style.height = `${height}px`;
        tempDiv.style.boxSizing = "border-box";
        tempDiv.style.background = "white"; // Set background color to avoid transparency

        const node = div.cloneNode(true) as HTMLDivElement;
        node.style.padding = `${paddingV}px ${paddingH}px`;
        tempDiv.appendChild(node);
        document.body.appendChild(tempDiv);

        // Use html2canvas to convert the temporary container to a canvas
        const canvas = await html2canvas(tempDiv, {
            scale: window.devicePixelRatio, // Ensure clarity on high-resolution devices
            useCORS: true, // Enable this option if the div contains cross-origin images
        });

        // Remove the temporary container
        document.body.removeChild(tempDiv);

        // Convert the canvas to a Blob object
        const blob = await new Promise<Blob>((resolve, reject) => {
            canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error("Failed to convert canvas to Blob."));
                }
            }, "image/png");
        });

        // Use the Clipboard API to write the Blob to the clipboard
        await navigator.clipboard.write([
            new ClipboardItem({
                [blob.type]: blob,
            }),
        ]);

        console.log("Image with padding successfully copied to clipboard!");

        return true;
    } catch (error) {
        console.error("Failed to export div to image and copy to clipboard:", error);
        throw error; // Throw the error for the caller to handle
    }
}

export function extractContentAfterDivider(text: string) {
    const divider = "---";
    const index = text.indexOf(divider);
    if (index !== -1 && index + divider.length < text.length) {
        return text.slice(index + divider.length).trim();
    }
    return text.trim();
}

export async function copyToClipboard(text: string) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand("copy");
            return true;
        } catch (error) {
            return false;
        }
        finally {
            document.body.removeChild(textArea);
        }
    }
}

export function getUrlSearchArg(argName: string) {
    const location = window.location;
    try {
        if (location.hash) {
            return new URLSearchParams(location.hash.split("?")[1]).get(argName)
        }
        else {
            return new URLSearchParams(location.search).get(argName)
        }
    }
    catch {
        return null;
    }
}

export function getDateStringByUnixTime(unixTimestamp?: number) {
    if (!unixTimestamp) {
        return "";
    }

    const date = new Date(unixTimestamp * 1000);
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);

    return '[' + year + '-' + month + '-' + day + ']';
}

export function raise_gtag_event(eventName: string, args = {}) {
    const dataLayer: any[] = (window as any)["dataLayer"] || [];
    dataLayer.push({
        event: eventName,
        ...args
    });
}

import { AnswerOptions, AnswerStyle, AnswerComplexity } from '../types/Base';

/**
 * Build extra_instruction based on answer options
 */
export function buildExtraInstruction(options: AnswerOptions): string {
    const parts: string[] = [];

    // Style instruction
    if (options.style === AnswerStyle.Beginner) {
        parts.push('请使用通俗易懂的语言解释，避免使用专业术语，必要时举例说明');
    } else if (options.style === AnswerStyle.Professional) {
        parts.push('请使用专业、严谨的语言回答，可以使用技术术语');
    }

    // Complexity instruction
    if (options.complexity === AnswerComplexity.Concise) {
        parts.push('回答尽量简洁扼要，突出重点');
    } else if (options.complexity === AnswerComplexity.Verbose) {
        parts.push('请详细全面地回答，提供更多背景信息和相关知识');
    }

    // Custom instruction
    if (options.customInstruction?.trim()) {
        parts.push(options.customInstruction.trim());
    }

    return parts.join('。');
}