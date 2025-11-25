import React, { useState } from 'react';

export default function ContributorList({ contributors }) {
  const [selectedContributor, setSelectedContributor] = useState(null);

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {contributors.map((contributor, index) => (
          <div 
            key={index}
            onClick={() => setSelectedContributor(contributor)}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-inner shrink-0">
              {contributor.name.charAt(0)}
            </div>
            <div>
              <h3 className="font-bold text-gray-900">{contributor.name}</h3>
              <p className="text-sm text-gray-500">{contributor.role}</p>
              {contributor.location && (
                <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                  {contributor.location}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedContributor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm" onClick={() => setSelectedContributor(null)}>
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl relative animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
            <button 
              onClick={() => setSelectedContributor(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            
            <div className="flex flex-col items-center text-center mb-8">
               <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-4xl shadow-inner mb-4">
                  {selectedContributor.name.charAt(0)}
               </div>
               <h2 className="text-2xl font-bold text-gray-900">{selectedContributor.name}</h2>
               <p className="text-blue-600 font-medium">{selectedContributor.role}</p>
            </div>

            <div className="space-y-4">
              {selectedContributor.email && (
                <div className="flex items-center gap-3 text-gray-600 p-3 bg-gray-50 rounded-lg">
                  <svg className="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                  <a href={`mailto:${selectedContributor.email}`} className="hover:text-blue-600 transition-colors break-all">{selectedContributor.email}</a>
                </div>
              )}
              
              {selectedContributor.location && (
                <div className="flex items-center gap-3 text-gray-600 p-3 bg-gray-50 rounded-lg">
                   <svg className="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                   <span>{selectedContributor.location}</span>
                </div>
              )}

              {selectedContributor.linkedin && (
                <div className="flex items-center gap-3 text-gray-600 p-3 bg-gray-50 rounded-lg">
                  <svg className="w-5 h-5 text-gray-400 shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
                  <a href={selectedContributor.linkedin} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 transition-colors">LinkedIn Profile</a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}