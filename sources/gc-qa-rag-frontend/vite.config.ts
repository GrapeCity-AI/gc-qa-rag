import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { createHtmlPlugin } from 'vite-plugin-html';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  console.log("mode", mode);

  const add_extra = mode === "production" ? true : false;

  const GA_KEY = "";
  const GC_AI_SEARCH_SERVER_URL = "";

  const EXTRA_PART1 = `<script>
      (function (w, d, s, l, i) {
        w[l] = w[l] || [];
        w[l].push({
          "gtm.start": new Date().getTime(),
          event: "gtm.js",
        });
        var f = d.getElementsByTagName(s)[0],
          j = d.createElement(s),
          dl = l != "dataLayer" ? "&l=" + l : "";
        j.async = true;
        j.src = "https://www.googletagmanager.com/gtm.js?id=" + i + dl;
        f.parentNode.insertBefore(j, f);
      })(window, document, "script", "dataLayer", "${GA_KEY}");
    </script>`

  const EXTRA_PART2 = `<script>
        window.GC_AI_SEARCH_SERVER_URL = "${GC_AI_SEARCH_SERVER_URL}";
    </script>`;

  return {
    build: {
      chunkSizeWarningLimit: 1024,
      rollupOptions: {
        treeshake: 'recommended',
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'antd-vendor': ['antd', '@ant-design/icons'],
            "remark-vendor": ['remark-gfm', 'remark-breaks', 'rehype-katex', 'rehype-highlight', 'remark-math'],
            'mermaid-vendor': ['mermaid'],
            'katex-vendor': ['katex'],
          }
        }
      }
    },
    plugins: [
      react(),
      createHtmlPlugin({
        inject: {
          data: {
            EXTRA_PART1: add_extra ? EXTRA_PART1 : "",
            EXTRA_PART2: add_extra ? EXTRA_PART2 : "",
          },
        },
      }),
    ],
  }
});
