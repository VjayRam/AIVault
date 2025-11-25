import React, { useState, useMemo, useEffect, useRef } from 'react';
import Fuse from 'fuse.js';

function CustomDropdown({ options, value, onChange, placeholder, formatText }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownRef]);

  return (
    <div className="relative flex-1" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-3 px-6 rounded-full border border-gray-300 shadow-sm hover:border-blue-400 focus:ring-2 focus:ring-blue-500 outline-none bg-white text-left flex justify-between items-center transition-all"
      >
        <span className={`block truncate ${value ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
          {value ? formatText(value) : placeholder}
        </span>
        <svg 
            className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-20 w-full mt-2 bg-white rounded-2xl shadow-xl border border-gray-100 max-h-60 overflow-y-auto py-2 animate-in fade-in slide-in-from-top-2 duration-200">
          <div
            className={`px-6 py-2.5 cursor-pointer hover:bg-blue-50 transition-colors ${value === '' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'}`}
            onClick={() => {
              onChange('');
              setIsOpen(false);
            }}
          >
            {placeholder}
          </div>
          {options.map((option) => (
            <div
              key={option}
              className={`px-6 py-2.5 cursor-pointer hover:bg-blue-50 transition-colors ${value === option ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'}`}
              onClick={() => {
                onChange(option);
                setIsOpen(false);
              }}
            >
              {formatText(option)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ComponentSearch({ components }) {
  const [searchInput, setSearchInput] = useState('');
  const [query, setQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [selectedAuthor, setSelectedAuthor] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedComponent, setSelectedComponent] = useState(null);

  const dateOptions = [
    'Last 24 Hours',
    'Last 7 Days',
    'Last 30 Days',
    'Last 6 Months',
    'Last 1 Year'
  ];

  const formatText = (text) => {
    if (!text) return '';
    return text
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

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
      keys: ['name', 'description', 'tags', 'author', 'comp_id'],
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

    if (selectedDate) {
      const now = new Date();
      filtered = filtered.filter(c => {
        if (!c.lastUpdated) return false;
        const updated = new Date(c.lastUpdated);
        const diffTime = Math.abs(now - updated);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        switch (selectedDate) {
          case 'Last 24 Hours': return diffDays <= 1;
          case 'Last 7 Days': return diffDays <= 7;
          case 'Last 30 Days': return diffDays <= 30;
          case 'Last 6 Months': return diffDays <= 180;
          case 'Last 1 Year': return diffDays <= 365;
          default: return true;
        }
      });
    }

    return filtered;
  }, [query, selectedTag, selectedAuthor, selectedDate, fuse, components]);

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <div className="mb-8 space-y-4">
        <form 
          onSubmit={(e) => { e.preventDefault(); setQuery(searchInput); }} 
          className="flex flex-col sm:flex-row gap-2"
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
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-full shadow-sm hover:from-blue-700 hover:to-indigo-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all w-full sm:w-auto"
          >
            Search
          </button>
        </form>
        
        <div className="flex flex-col md:flex-row gap-4">
          <CustomDropdown
            options={uniqueTags}
            value={selectedTag}
            onChange={setSelectedTag}
            placeholder="All Tags"
            formatText={formatText}
          />

          <CustomDropdown
            options={uniqueAuthors}
            value={selectedAuthor}
            onChange={setSelectedAuthor}
            placeholder="All Authors"
            formatText={formatText}
          />

          <CustomDropdown
            options={dateOptions}
            value={selectedDate}
            onChange={setSelectedDate}
            placeholder="Any Time"
            formatText={(t) => t}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {results.map((component) => (
          <div
            key={component.path}
            onClick={() => setSelectedComponent(component)}
            className="block p-6 bg-white rounded-xl border border-gray-200 hover:border-blue-500 hover:ring-1 hover:ring-blue-500 transition-all cursor-pointer"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-xl font-bold text-gray-900">{component.name}</h3>
              {component.comp_id && (
                <span className="text-xs text-gray-400 font-mono bg-gray-50 px-2 py-1 rounded" title="Component ID">
                  {component.comp_id}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mb-2">By {formatText(component.author) || 'Unknown'}</p>
            <p className="text-gray-600 mb-4">{component.description}</p>
            <div className="flex flex-wrap gap-2">
              {component.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                >
                  {formatText(tag)}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {results.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          No components found matching "{query}"
        </div>
      )}

      {selectedComponent && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedComponent(null)}>
          <div className="bg-white rounded-2xl p-6 md:p-8 max-w-2xl w-full shadow-2xl relative max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <button 
                onClick={() => setSelectedComponent(null)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            
            <div className="flex justify-between items-start mb-4 pr-8">
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 break-words">{selectedComponent.name}</h2>
                 {selectedComponent.comp_id && (
                    <span className="text-sm text-gray-500 font-mono bg-gray-100 px-3 py-1 rounded-full whitespace-nowrap ml-2">
                      {selectedComponent.comp_id}
                    </span>
                  )}
            </div>

            <p className="text-lg text-gray-600 mb-2">By <span className="font-semibold text-gray-800">{formatText(selectedComponent.author) || 'Unknown'}</span></p>
            {selectedComponent.lastUpdated && (
                <p className="text-sm text-gray-500 mb-4 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    Updated on {selectedComponent.lastUpdated}
                </p>
            )}
            
            <div className="flex flex-wrap gap-2 mb-6">
              {selectedComponent.tags.map((tag) => (
                <span key={tag} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                  {formatText(tag)}
                </span>
              ))}
            </div>

            <p className="text-gray-700 mb-8 leading-relaxed">{selectedComponent.description}</p>

            <div className="flex flex-col sm:flex-row justify-end gap-4">
                <button 
                    onClick={() => setSelectedComponent(null)}
                    className="px-6 py-2 text-gray-600 hover:text-gray-800 font-medium w-full sm:w-auto text-center"
                >
                    Close
                </button>
                <a 
                    href={selectedComponent.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2 w-full sm:w-auto"
                >
                    <span>View on GitHub</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}