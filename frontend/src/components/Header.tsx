import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.793L4.5 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.5l3.883-3.707zM12.5 8a1 1 0 011-1h1a1 1 0 011 1v4a1 1 0 01-1 1h-1a1 1 0 01-1-1V8z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Audio Processor</h1>
              <p className="text-sm text-gray-500">Speech Analysis Dashboard</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-6">
            <Link 
              to="/" 
              className="text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              Dashboard
            </Link>
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              API Docs
            </a>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-500">System Online</span>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 