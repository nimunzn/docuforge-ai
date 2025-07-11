import React, { useState, useEffect } from 'react';
import { ChevronDown, Settings, Zap } from 'lucide-react';
import { useDocumentStore } from '../../store/useDocumentStore';
import { aiAPI } from '../../services/api';

export const ProviderSelector: React.FC = () => {
  const {
    providers,
    setProviders,
    currentProvider,
    setCurrentProvider,
    currentModel,
    setCurrentModel,
    setError
  } = useDocumentStore();
  
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    loadProviders();
  }, []);
  
  const loadProviders = async () => {
    try {
      setIsLoading(true);
      const response = await aiAPI.getProviders();
      setProviders(response.data.providers);
      setCurrentProvider(response.data.default);
      
      // Set default model for the current provider
      const defaultProvider = response.data.providers[response.data.default];
      if (defaultProvider && defaultProvider.models.length > 0) {
        setCurrentModel(defaultProvider.models[0]);
      }
    } catch (error) {
      setError('Failed to load AI providers');
      console.error('Error loading providers:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleProviderChange = (provider: string) => {
    setCurrentProvider(provider);
    
    // Set default model for the new provider
    const providerData = providers[provider];
    if (providerData && providerData.models.length > 0) {
      setCurrentModel(providerData.models[0]);
    }
    
    setIsOpen(false);
  };
  
  const handleModelChange = (model: string) => {
    setCurrentModel(model);
    setIsOpen(false);
  };
  
  const currentProviderData = providers[currentProvider];
  
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Zap className="w-4 h-4" />
        Loading...
      </div>
    );
  }
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        <Zap className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium">
          {currentProviderData?.name || currentProvider} · {currentModel}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-900">AI Provider</h3>
          </div>
          
          <div className="py-2">
            {Object.entries(providers).map(([key, provider]) => (
              <div key={key} className="px-3 py-2 hover:bg-gray-50">
                <button
                  onClick={() => handleProviderChange(key)}
                  className={`w-full text-left flex items-center justify-between ${
                    currentProvider === key ? 'text-blue-600' : 'text-gray-700'
                  }`}
                >
                  <div>
                    <div className="font-medium">{provider.name}</div>
                    <div className="text-xs text-gray-500">
                      {provider.models.length} models available
                    </div>
                  </div>
                  
                  <div className={`w-2 h-2 rounded-full ${
                    provider.available ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                </button>
              </div>
            ))}
          </div>
          
          {currentProviderData && (
            <>
              <div className="px-3 py-2 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Model</h4>
                <div className="space-y-1">
                  {currentProviderData.models.map((model) => (
                    <button
                      key={model}
                      onClick={() => handleModelChange(model)}
                      className={`w-full text-left px-2 py-1 rounded text-sm ${
                        currentModel === model
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {model}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
          
          <div className="px-3 py-2 border-t border-gray-200">
            <button className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
              <Settings className="w-4 h-4" />
              Provider Settings
            </button>
          </div>
        </div>
      )}
      
      {/* Overlay to close dropdown */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};