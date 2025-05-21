import { useState, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { ProductType, SearchMode } from "../../../types/Base";
import { RetrivalItem } from "../types";
import { getUrlSearchArg } from "../../../common/utils";

export const useSearchState = () => {
  const queryArg = getUrlSearchArg("query") ?? "";
  let productArg =
    getUrlSearchArg("product") ??
    localStorage.getItem("gcai-product") ??
    ProductType.Forguncy;
  let searchModeArg =
    getUrlSearchArg("searchmode") ??
    sessionStorage.getItem("gcai-searchmode") ??
    SearchMode.Chat;

  if (
    productArg !== ProductType.Forguncy &&
    productArg !== ProductType.Wyn &&
    productArg !== ProductType.SpreadJS &&
    productArg !== ProductType.GcExcel
  ) {
    productArg = ProductType.Forguncy;
  }

  if (searchModeArg !== SearchMode.Chat && searchModeArg !== SearchMode.Think) {
    searchModeArg = SearchMode.Chat;
  }

  const [productType, setProductType] = useState(productArg as ProductType);
  const [searchMode, setSearchMode] = useState(searchModeArg as SearchMode);
  const [inputValue, setInputValue] = useState(queryArg);
  const [retrivals, setRetrivals] = useState<RetrivalItem[]>([]);
  const [controller, setController] = useState<AbortController>();
  const shouldSearchOnModeChange = useRef(false);
  const retrivalsUUID = useRef(uuidv4());
  const appendMessageMap = useRef(new Map());

  return {
    productType,
    setProductType,
    searchMode,
    setSearchMode,
    inputValue,
    setInputValue,
    retrivals,
    setRetrivals,
    controller,
    setController,
    shouldSearchOnModeChange,
    retrivalsUUID,
    appendMessageMap,
  };
}; 