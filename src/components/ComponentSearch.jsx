import React, { useState, useMemo } from 'react';
import Fuse from 'fuse.js';

export default function ComponentSearch({ components }) {
  const [searchInput, setSearchInput] = useState('');
  const [query, setQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [selectedAuthor, setSelectedAuthor] = useState('');

  const uniqueTags = useMemo(() => {
    const tags = new Set();
    components.forEach(c => c.tags?.forEach(t => tags.add(t)));
    return Array.from(tags).sort();
  }, [components]);

  const uniqueAuthors = useMemo(() => {
    const authors = new Set();
    components.forEach(c => {
      if (c.author) authors.add(c.author);
    });
    return Array.from(authors).sort();
  }, [components]);

  const fuse = useMemo(() => {
    return new Fuse(components, {
      keys: ['name', 'description', 'tags', 'author'],
      threshold: 0.3,
    });
  }, [components]);

  const results = useMemo(() => {
    let filtered = components;

    if (query) {
      filtered = fuse.search(query).map((result) => result.item);
    }

    if (selectedTag) {
      filtered = filtered.filter(c => c.tags?.includes(selectedTag));
    }

    if (selectedAuthor) {
      filtered = filtered.filter(c => c.author === selectedAuthor);
    }

    return filtered;
  }, [query, selectedTag, selectedAuthor, fuse, components]);

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <div className="mb-8 space-y-4">
        <form 
          onSubmit={(e) => { e.preventDefault(); setQuery(searchInput); }} 
          className="flex gap-2"
        >
          <input
            type="text"
            placeholder="Search AI components..."
            className="flex-1 p-4 px-6 rounded-full border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button
            type="submit"
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-full shadow-sm hover:from-blue-700 hover:to-indigo-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all"
          >
            Search
          </button>
        </form>
        
        <div className="flex gap-4">
          <select
            className="flex-1 p-3 px-6 rounded-full border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white"
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
          >
            <option value="">All Tags</option>
            {uniqueTags.map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>

          <select
            className="flex-1 p-3 px-6 rounded-full border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white"
            value={selectedAuthor}
            onChange={(e) => setSelectedAuthor(e.target.value)}
          >
            <option value="">All Authors</option>
            {uniqueAuthors.map(author => (
              <option key={author} value={author}>{author}</option>
            ))}
          </select>
        </div>
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
            <p className="text-sm text-gray-500 mb-2">By {component.author || 'Unknown'}</p>
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