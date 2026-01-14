import { useState, useCallback } from 'react';
import { AnswerOptions, AnswerStyle, AnswerComplexity, DEFAULT_ANSWER_OPTIONS } from '../types/Base';
import { getUrlSearchArg } from '../common/utils';

const STORAGE_KEY = 'gcai-answer-options';

/**
 * Update URL parameter without navigation (supports hash routing)
 */
const updateUrlParam = (key: string, value: string | null) => {
    const location = window.location;

    if (location.hash) {
        // Hash routing: /#/search?query=xxx
        const hashParts = location.hash.split('?');
        const basePath = hashParts[0];
        const params = new URLSearchParams(hashParts[1] || '');

        if (value) {
            params.set(key, value);
        } else {
            params.delete(key);
        }

        const newHash = params.toString() ? `${basePath}?${params.toString()}` : basePath;
        window.history.replaceState({}, '', `${location.pathname}${newHash}`);
    } else {
        // Normal routing
        const url = new URL(location.href);
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        window.history.replaceState({}, '', url.toString());
    }
};

/**
 * Get answer options from URL parameters
 */
const getOptionsFromUrl = (): Partial<AnswerOptions> => {
    const style = getUrlSearchArg('style');
    const complexity = getUrlSearchArg('complexity');
    const customInstruction = getUrlSearchArg('custom');

    const options: Partial<AnswerOptions> = {};

    if (style === AnswerStyle.Beginner || style === AnswerStyle.Professional) {
        options.style = style;
    }
    if (complexity === AnswerComplexity.Concise || complexity === AnswerComplexity.Verbose) {
        options.complexity = complexity;
    }
    if (customInstruction) {
        options.customInstruction = decodeURIComponent(customInstruction);
    }

    return options;
};

/**
 * Get answer options from localStorage
 */
const getOptionsFromStorage = (): Partial<AnswerOptions> => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch (e) {
        console.error('Failed to parse answer options from storage:', e);
    }
    return {};
};

/**
 * Initialize answer options (priority: URL > localStorage > default)
 */
const getInitialOptions = (): AnswerOptions => {
    const urlOptions = getOptionsFromUrl();
    const storageOptions = getOptionsFromStorage();

    return {
        ...DEFAULT_ANSWER_OPTIONS,
        ...storageOptions,
        ...urlOptions,
    };
};

export const useAnswerOptions = () => {
    const [options, setOptions] = useState<AnswerOptions>(getInitialOptions);

    // Update options and persist to localStorage
    const updateOptions = useCallback((newOptions: Partial<AnswerOptions>) => {
        setOptions(prev => {
            const updated = { ...prev, ...newOptions };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
            return updated;
        });
    }, []);

    // Set style
    const setStyle = useCallback((style: AnswerStyle) => {
        updateOptions({ style });
    }, [updateOptions]);

    // Set complexity
    const setComplexity = useCallback((complexity: AnswerComplexity) => {
        updateOptions({ complexity });
    }, [updateOptions]);

    // Set custom instruction
    const setCustomInstruction = useCallback((customInstruction: string) => {
        updateOptions({ customInstruction });
        updateUrlParam('custom', customInstruction || null);
    }, [updateOptions]);

    // Build URL parameters string
    const buildUrlParams = useCallback((): string => {
        const params: string[] = [];
        params.push(`style=${encodeURIComponent(options.style)}`);
        params.push(`complexity=${encodeURIComponent(options.complexity)}`);
        if (options.customInstruction) {
            params.push(`custom=${encodeURIComponent(options.customInstruction)}`);
        }
        return params.join('&');
    }, [options]);

    return {
        options,
        setStyle,
        setComplexity,
        setCustomInstruction,
        updateOptions,
        buildUrlParams,
    };
};
