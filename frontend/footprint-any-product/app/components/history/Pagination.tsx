import React from 'react';
import { PaginationProps } from '../../types';

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange
}) => {
  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    // Always show the first page
    pages.push(1);
    
    // Calculate range of pages to show around current page
    let startPage = Math.max(2, currentPage - Math.floor((maxPagesToShow - 3) / 2));
    const endPage = Math.min(totalPages - 1, startPage + maxPagesToShow - 3);
    
    // Adjust startPage if endPage is maxed out
    if (endPage === totalPages - 1) {
      startPage = Math.max(2, endPage - (maxPagesToShow - 3));
    }
    
    // Add "..." if there's a gap after page 1
    if (startPage > 2) {
      pages.push('...');
    }
    
    // Add middle pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    // Add "..." if there's a gap before the last page
    if (endPage < totalPages - 1) {
      pages.push('...');
    }
    
    // Always show the last page if there's more than one page
    if (totalPages > 1) {
      pages.push(totalPages);
    }
    
    return pages;
  };
  
  // Don't render pagination if there's only one page or no pages
  if (totalPages <= 1) {
    return null;
  }
  
  return (
    <div className="flex justify-center items-center my-6">
      <nav className="inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
        {/* Previous Page Button */}
        <button
          onClick={() => currentPage > 1 && onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="eco-button px-2 py-2 rounded-l-md"
          style={{ 
            backgroundColor: 'var(--button-hover)',
            border: '1px solid var(--card-border)',
            color: currentPage === 1 ? 'var(--score-neutral)' : 'var(--foreground)',
            cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
            opacity: currentPage === 1 ? 0.5 : 1
          }}
        >
          <span className="sr-only">Previous</span>
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </button>
        
        {/* Page Numbers */}
        {getPageNumbers().map((page, index) => (
          <React.Fragment key={index}>
            {page === '...' ? (
              <span
                className="px-4 py-2"
                style={{ 
                  backgroundColor: 'var(--button-hover)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--score-neutral)'
                }}
              >
                ...
              </span>
            ) : (
              <button
                onClick={() => typeof page === 'number' && onPageChange(page)}
                className="eco-button px-4 py-2"
                style={{ 
                  backgroundColor: currentPage === page ? 'var(--primary)' : 'var(--button-hover)',
                  border: '1px solid var(--card-border)',
                  color: currentPage === page ? 'white' : 'var(--foreground)'
                }}
                aria-current={currentPage === page ? 'page' : undefined}
              >
                {page}
              </button>
            )}
          </React.Fragment>
        ))}
        
        {/* Next Page Button */}
        <button
          onClick={() => currentPage < totalPages && onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="eco-button px-2 py-2 rounded-r-md"
          style={{ 
            backgroundColor: 'var(--button-hover)',
            border: '1px solid var(--card-border)',
            color: currentPage === totalPages ? 'var(--score-neutral)' : 'var(--foreground)',
            cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
            opacity: currentPage === totalPages ? 0.5 : 1
          }}
        >
          <span className="sr-only">Next</span>
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </button>
      </nav>
    </div>
  );
};

export default Pagination;