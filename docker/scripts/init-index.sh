#!/bin/sh
# Docker initialization script for document indexing
# This script runs as part of the indexer service before the backend starts

set -e

CHROMA_DIR="${CHROMA_PERSIST_DIR:-/app/data/chroma_db}"
DOCUMENTS_DIR="/app/data/documents"
REINDEX_FLAG="$DOCUMENTS_DIR/.reindex"

echo "========================================"
echo "RAG Chatbot - Document Indexer"
echo "========================================"
echo "ChromaDB directory: $CHROMA_DIR"
echo "Documents directory: $DOCUMENTS_DIR"
echo ""

# Function to get document count from ChromaDB
get_chroma_doc_count() {
    python3 -c "
import sys
try:
    import chromadb
    from chromadb.config import Settings
    client = chromadb.PersistentClient(
        path='$CHROMA_DIR',
        settings=Settings(anonymized_telemetry=False)
    )
    try:
        collection = client.get_collection('documents')
        print(collection.count())
    except:
        print(0)
except Exception as e:
    print(0)
" 2>/dev/null
}

# Function to check if ChromaDB has indexed documents
is_chroma_empty() {
    if [ ! -d "$CHROMA_DIR" ]; then
        return 0  # Directory doesn't exist = empty
    fi

    # Check actual document count in ChromaDB
    doc_count=$(get_chroma_doc_count)
    echo "   Current indexed documents: $doc_count"

    if [ "$doc_count" -eq 0 ]; then
        return 0  # No documents indexed = empty
    fi

    return 1  # Has indexed documents
}

# Function to check if reindex flag exists
should_reindex() {
    if [ -f "$REINDEX_FLAG" ]; then
        return 0  # Reindex requested
    fi
    return 1
}

# Function to count documents
count_documents() {
    find "$DOCUMENTS_DIR" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' '
}

# Function to run indexing
run_indexing() {
    local doc_count=$(count_documents)

    if [ "$doc_count" -eq 0 ]; then
        echo "⚠️  No markdown documents found in $DOCUMENTS_DIR"
        echo "   Skipping indexing."
        return 0
    fi

    echo "📄 Found $doc_count markdown document(s)"
    echo "🔄 Starting document indexing..."
    echo ""

    # Run the indexing script with --reset to ensure clean state
    python /app/scripts/index_documents.py \
        --source "$DOCUMENTS_DIR" \
        --persist-dir "$CHROMA_DIR" \
        --reset

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Indexing completed successfully!"
    else
        echo ""
        echo "❌ Indexing failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Main logic
echo "Checking indexing conditions..."
echo ""

if is_chroma_empty; then
    echo "📦 ChromaDB is empty (first run)"
    echo "   → Will index documents"
    echo ""
    run_indexing
elif should_reindex; then
    echo "🔄 Reindex flag detected (.reindex file)"
    echo "   → Will re-index documents"
    echo ""

    # Remove the reindex flag
    rm -f "$REINDEX_FLAG"
    echo "   Removed .reindex flag"
    echo ""

    run_indexing
else
    echo "✅ Using existing index"
    echo "   ChromaDB already contains indexed documents."
    echo ""
    echo "   To trigger re-indexing, create a .reindex file:"
    echo "   touch $DOCUMENTS_DIR/.reindex"
    echo ""
fi

echo "========================================"
echo "Initialization complete"
echo "========================================"
