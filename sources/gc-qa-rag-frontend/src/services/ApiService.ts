import { fetchEventSource } from "@microsoft/fetch-event-source";
import { MessageItem } from "../types/Api";

class RetriableError extends Error { }
class FatalError extends Error { }

const URL_ROOT = ((window as any).GC_AI_SEARCH_SERVER_URL) || (window.location.protocol + "//" + window.location.hostname + ":8000");
//const URL_ROOT = (window.location.protocol + "//" + window.location.hostname + ":8000");

export const getSearchResult = async (
  keyword: string,
  mode: string,
  product: string,
  session_id: string,
  session_index: number,
) => {
  const url = `${URL_ROOT}/search/`;

  const requestBody = {
    keyword: keyword,
    mode: mode,
    product: product,
    session_id: session_id,
    session_index: session_index,
  };

  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  }).then((res) => res.json());
};

export const getChatResult = async (
  keyword: string,
  messages: MessageItem[],
  product: string,
  callback: (chunk: string, end: boolean) => void,
  onController: (controller: AbortController) => void,
  extraInstruction: string = ""
) => {
  const url = `${URL_ROOT}/chat_streaming/`;

  const requestBody = JSON.stringify({
    keyword: keyword,
    messages: messages,
    product: product,
    extra_instruction: extraInstruction,
  });

  const controller = new AbortController();
  if (onController) {
    onController(controller);
  }
  await new Promise(() => {
    fetchEventSource(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: requestBody,
      signal: controller.signal,
      openWhenHidden:true,
      async onopen(response) {
        if (response.ok) {
          return;
        } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          throw new FatalError();
        } else {
          throw new RetriableError();
        }
      },
      onmessage(msg) {
        // if the server emits an error message, throw an exception
        // so it gets handled by the onerror callback below:
        if (msg.event === 'FatalError') {
          throw new FatalError(msg.data);
        }
        callback?.(JSON.parse(msg.data)["text"], false);
      },
      onclose() {
        callback?.("", false);
      },
      onerror(err) {
        callback?.("", false);
        if (err instanceof FatalError) {
          throw err; // rethrow to stop the operation
        } else {
          // do nothing to automatically retry. You can also
          // return a specific retry interval here.
        }
      }
    }).finally(() => {
      if (controller.signal.aborted) {
        callback?.("\n\n> [Terminated]", true);
      } else {
        callback?.("", true);
      }
    });
  });
};

export const getThinkResult = async (
  keyword: string,
  messages: MessageItem[],
  product: string,
  callback: (chunk: string, end: boolean) => void,
  onController: (controller: AbortController) => void,
  extraInstruction: string = ""
) => {
  const url = `${URL_ROOT}/think_streaming/`;

  const requestBody = JSON.stringify({
    keyword: keyword,
    messages: messages,
    product: product,
    extra_instruction: extraInstruction,
  });

  const controller = new AbortController();
  if (onController) {
    onController(controller);
  }
  await new Promise(() => {
    fetchEventSource(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: requestBody,
      signal: controller.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (response.ok) {
          return;
        } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          throw new FatalError();
        } else {
          throw new RetriableError();
        }
      },
      onmessage(msg) {
        // if the server emits an error message, throw an exception
        // so it gets handled by the onerror callback below:
        if (msg.event === 'FatalError') {
          throw new FatalError(msg.data);
        }
        callback?.(JSON.parse(msg.data)["text"], false);
      },
      onclose() {
        callback?.("", false);
      },
      onerror(err) {
        callback?.("", false);
        if (err instanceof FatalError) {
          throw err; // rethrow to stop the operation
        } else {
          // do nothing to automatically retry. You can also
          // return a specific retry interval here.
        }
      }
    }).finally(() => {
      if (controller.signal.aborted) {
        callback?.("\n\n> [Terminated]", true);
      } else {
        callback?.("", true);
      }
    });
  });
};

export const getFeedbackResult = async (
  question: string,
  answer: string,
  rating: number,
  comments: string,
  product: string,
) => {
  const url = `${URL_ROOT}/feedback/`;

  const requestBody = {
    question: question,
    answer: answer,
    rating: rating,
    comments: comments,
    product: product,
  };

  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  }).then((res) => res.json());
};

export const getProductsResult = async (mode: string = "fixed") => {
  const url = `${URL_ROOT}/products/?mode=${encodeURIComponent(mode)}`;

  return fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  }).then((res) => res.json());
};
