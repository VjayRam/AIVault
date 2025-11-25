import React, { useState, useMemo } from 'react';
import Fuse from 'fuse.js';

export default function ComponentSearch({ components }) {
  const [query, setQuery] = useState('');

  const fuse = useMemo(() => {
    return new Fuse(components, {
      keys: ['name', 'description', 'tags'],
      threshold: 0.3,
    });
  }, [components]);

  const results = useMemo(() => {
    if (!query) return components;
    return fuse.search(query).map((result) => result.item);
  }, [query, fuse, components]);

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <div className="mb-8">
        <input
          type="text"
          placeholder="Search AI components..."
          className="w-full p-4 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {results.map((component) => (
          <a
            key={component.path}
            href={component.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-2">{component.name}</h3>
            <p className="text-gray-600 mb-4">{component.description}</p>
            <div className="flex flex-wrap gap-2">
              {component.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </a>
        ))}
      </div>
      
      {results.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          No components found matching "{query}"
        </div>
      )}
    </div>
  );
}