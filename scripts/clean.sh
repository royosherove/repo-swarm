#!/bin/bash

echo "🧹 Cleaning up temp folders..."

# Clean investigator temp folder
if [ -d "src/investigator/temp" ]; then
    echo "Removing src/investigator/temp and all contents..."
    rm -rf src/investigator/temp
    echo "✅ Investigator temp folder cleaned successfully!"
else
    echo "ℹ️  No investigator temp folder found to clean."
fi

# Clean root temp folder
if [ -d "temp" ]; then
    echo "Removing temp/ and all contents..."
    rm -rf temp
    echo "✅ Root temp folder cleaned successfully!"
else
    echo "ℹ️  No root temp folder found to clean."
fi

echo "🎉 All temp folders cleaned!" 