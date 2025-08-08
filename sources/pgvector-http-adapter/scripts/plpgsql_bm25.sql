-- plpgsql_bm25.sql
-- BM25 search implemented in PL/pgSQL
-- Source: https://github.com/jankovicsandras/plpgsql_bm25

-- Helper function for simple tokenization
CREATE OR REPLACE FUNCTION bm25simpletokenize(txt TEXT)
RETURNS TEXT[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Simple whitespace tokenization with basic cleanup
    RETURN string_to_array(
        regexp_replace(
            lower(trim(txt)),
            '[^\w\s]', ' ', 'g'
        ),
        ' '
    );
END;
$$;

-- Stopword filter for English
CREATE OR REPLACE FUNCTION stopwordfilter(words TEXT[], language TEXT DEFAULT 'en')
RETURNS TEXT[]
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    stopwords TEXT[];
    filtered_words TEXT[] := '{}';
    word TEXT;
BEGIN
    -- English stopwords
    IF language = 'en' OR language = '' THEN
        stopwords := ARRAY['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                          'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
                          'to', 'was', 'will', 'with', 'but', 'have', 'this', 'or', 'not'];
    ELSE
        stopwords := '{}';
    END IF;

    FOREACH word IN ARRAY words
    LOOP
        IF word != '' AND NOT (word = ANY(stopwords)) THEN
            filtered_words := array_append(filtered_words, word);
        END IF;
    END LOOP;

    RETURN filtered_words;
END;
$$;

-- Create BM25 index
CREATE OR REPLACE FUNCTION bm25createindex(
    tablename TEXT,
    columnname TEXT,
    algo TEXT DEFAULT '',
    stopwordslanguage TEXT DEFAULT 'en'
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    docstname TEXT;
    wordstname TEXT;
    sql_cmd TEXT;
    doc_record RECORD;
    words TEXT[];
    word TEXT;
    doc_id INTEGER;
    word_count INTEGER;
BEGIN
    -- Generate table names
    docstname := tablename || '_' || columnname || '_bm25i_docs' || algo;
    wordstname := tablename || '_' || columnname || '_bm25i_words' || algo;

    -- Drop existing tables
    EXECUTE 'DROP TABLE IF EXISTS ' || docstname;
    EXECUTE 'DROP TABLE IF EXISTS ' || wordstname;

    -- Create docs table
    sql_cmd := 'CREATE TABLE ' || docstname || ' (
        id SERIAL PRIMARY KEY,
        doc TEXT NOT NULL,
        doc_length INTEGER DEFAULT 0
    )';
    EXECUTE sql_cmd;

    -- Create words table
    sql_cmd := 'CREATE TABLE ' || wordstname || ' (
        word TEXT NOT NULL,
        doc_id INTEGER NOT NULL,
        tf INTEGER DEFAULT 0,
        PRIMARY KEY(word, doc_id)
    )';
    EXECUTE sql_cmd;

    -- Insert documents and calculate word frequencies
    sql_cmd := 'SELECT ' || columnname || ' as content FROM ' || tablename;
    FOR doc_record IN EXECUTE sql_cmd
    LOOP
        -- Tokenize and filter stopwords
        words := stopwordfilter(bm25simpletokenize(doc_record.content), stopwordslanguage);

        -- Insert document
        sql_cmd := 'INSERT INTO ' || docstname || ' (doc, doc_length) VALUES ($1, $2) RETURNING id';
        EXECUTE sql_cmd INTO doc_id USING doc_record.content, array_length(words, 1);

        -- Count word frequencies
        FOREACH word IN ARRAY words
        LOOP
            sql_cmd := 'INSERT INTO ' || wordstname || ' (word, doc_id, tf)
                       VALUES ($1, $2, 1)
                       ON CONFLICT (word, doc_id)
                       DO UPDATE SET tf = ' || wordstname || '.tf + 1';
            EXECUTE sql_cmd USING word, doc_id;
        END LOOP;
    END LOOP;

    -- Create indexes for performance
    EXECUTE 'CREATE INDEX ON ' || wordstname || ' (word)';
    EXECUTE 'CREATE INDEX ON ' || wordstname || ' (doc_id)';

    RAISE NOTICE 'BM25 index created successfully for %.%', tablename, columnname;
END;
$$;

-- BM25 search function
CREATE OR REPLACE FUNCTION bm25topk(
    tablename TEXT,
    columnname TEXT,
    mquery TEXT,
    k INTEGER,
    algo TEXT DEFAULT '',
    stopwordslanguage TEXT DEFAULT 'en'
)
RETURNS TABLE(id INTEGER, score DOUBLE PRECISION, doc TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    docstname TEXT;
    wordstname TEXT;
    query_words TEXT[];
    total_docs INTEGER;
    avg_doc_length DOUBLE PRECISION;
    k1 DOUBLE PRECISION := 1.2;
    b DOUBLE PRECISION := 0.75;
    sql_cmd TEXT;
BEGIN
    -- Generate table names
    docstname := tablename || '_' || columnname || '_bm25i_docs' || algo;
    wordstname := tablename || '_' || columnname || '_bm25i_words' || algo;

    -- Tokenize query
    query_words := stopwordfilter(bm25simpletokenize(mquery), stopwordslanguage);

    -- Get corpus statistics
    EXECUTE 'SELECT COUNT(*) FROM ' || docstname INTO total_docs;
    EXECUTE 'SELECT AVG(doc_length) FROM ' || docstname INTO avg_doc_length;

    -- Build and execute BM25 query
    sql_cmd := '
    WITH doc_scores AS (
        SELECT
            d.id,
            d.doc,
            d.doc_length,
            COALESCE(SUM(
                LOG((CAST(' || total_docs || ' AS DOUBLE PRECISION) - df.df + 0.5) / (df.df + 0.5)) *
                (w.tf * (' || k1 || ' + 1)) /
                (w.tf + ' || k1 || ' * (1 - ' || b || ' + ' || b || ' * d.doc_length / ' || avg_doc_length || '))
            ), 0) as bm25_score
        FROM ' || docstname || ' d
        LEFT JOIN ' || wordstname || ' w ON d.id = w.doc_id AND w.word = ANY($1)
        LEFT JOIN (
            SELECT word, COUNT(DISTINCT doc_id) as df
            FROM ' || wordstname || '
            WHERE word = ANY($1)
            GROUP BY word
        ) df ON w.word = df.word
        GROUP BY d.id, d.doc, d.doc_length
        ORDER BY bm25_score DESC
        LIMIT ' || k || '
    )
    SELECT d.id::INTEGER, d.bm25_score, d.doc FROM doc_scores d';

    RETURN QUERY EXECUTE sql_cmd USING query_words;
END;
$$;