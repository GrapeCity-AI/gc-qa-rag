## Install

```
pnpm i
```

## Dev

```
pnpm run dev
```

## Build

```
pnpm run build
```

## Docker

```
docker build -t rag-frontend .
```

## GA Events

You can configure GA key in `vite.config.js`

- home.enter 首页搜索
- search.enter 搜索页搜索
- search.answer.like 有用
- search.answer.dislike 没用
- search.answer.copy 复制
- search.answer.copy_image 复制图像
- search.answer.append 追问
- search.hit.expand 搜索结果展开更多
- search.hit.navigate 搜索结果导航到来源链接
- search.gohome 回到首页
