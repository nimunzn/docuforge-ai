import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  Brain, 
  FileText, 
  PenTool, 
  Search, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Loader2,
  Zap
} from 'lucide-react';

export interface AgentActivity {
  agent: string;
  action: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  startTime: string;
  endTime?: string;
  input?: string;
  output?: string;
  error?: string;
  metadata?: Record<string, any>;
}

export interface AgentProcessData {
  activities: AgentActivity[];
  currentStep?: number;
  totalSteps?: number;
  startTime: string;
  endTime?: string;
  processingTime?: number;
}

interface AgentProcessDropdownProps {
  processData: AgentProcessData;
  isActive?: boolean;
}

export const AgentProcessDropdown: React.FC<AgentProcessDropdownProps> = ({ 
  processData, 
  isActive = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedActivities, setExpandedActivities] = useState<Set<number>>(new Set());

  const getAgentIcon = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'orchestrator':
        return <Zap className="w-4 h-4" />;
      case 'planner':
        return <Brain className="w-4 h-4" />;
      case 'writer':
        return <PenTool className="w-4 h-4" />;
      case 'reviewer':
        return <Search className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'pending':
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const calculateDuration = (startTime: string, endTime?: string) => {
    try {
      const start = new Date(startTime);
      const end = endTime ? new Date(endTime) : new Date();
      
      // Check if dates are valid
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return '0ms';
      }
      
      const diff = end.getTime() - start.getTime();
      
      // Ensure non-negative duration
      if (diff < 0) {
        return '0ms';
      }
      
      return diff < 1000 ? `${diff}ms` : `${(diff / 1000).toFixed(1)}s`;
    } catch (error) {
      console.error('Error calculating duration:', error, { startTime, endTime });
      return '0ms';
    }
  };

  const toggleActivityExpanded = (index: number) => {
    const newExpanded = new Set(expandedActivities);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedActivities(newExpanded);
  };

  const completedActivities = processData.activities.filter(a => a.status === 'completed').length;
  const totalActivities = processData.activities.length;
  const progressPercentage = totalActivities > 0 ? (completedActivities / totalActivities) * 100 : 0;

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50 mb-3">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <Brain className="w-4 h-4 text-purple-600" />
          <span className="font-medium text-gray-900">
            {isActive ? 'Thinking...' : 'Agent Process'}
          </span>
          {!isActive && (
            <span className="text-sm text-gray-500">
              ({completedActivities}/{totalActivities} completed)
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {processData.processingTime && (
            <span className="text-xs text-gray-500">
              {processData.processingTime.toFixed(1)}s
            </span>
          )}
          {isActive && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
        </div>
      </button>

      {/* Progress Bar */}
      {!isExpanded && totalActivities > 0 && (
        <div className="px-4 pb-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-white">
          {processData.activities.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No agent activities yet
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {processData.activities.map((activity, index) => (
                <div key={index} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                      {getAgentIcon(activity.agent)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 capitalize">
                            {activity.agent}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(activity.status)}`}>
                            {activity.status.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {getStatusIcon(activity.status)}
                          <span className="text-xs text-gray-500">
                            {formatTime(activity.startTime)}
                          </span>
                          {activity.endTime && (
                            <span className="text-xs text-gray-400">
                              ({calculateDuration(activity.startTime, activity.endTime)})
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-700 mb-2">
                        {activity.action}
                      </div>
                      
                      {(activity.input || activity.output || activity.error) && (
                        <div className="mt-2">
                          <button
                            onClick={() => toggleActivityExpanded(index)}
                            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                          >
                            {expandedActivities.has(index) ? (
                              <>
                                <ChevronDown className="w-3 h-3" />
                                Hide details
                              </>
                            ) : (
                              <>
                                <ChevronRight className="w-3 h-3" />
                                Show details
                              </>
                            )}
                          </button>
                          
                          {expandedActivities.has(index) && (
                            <div className="mt-2 space-y-2">
                              {activity.input && (
                                <div className="bg-blue-50 p-2 rounded text-xs">
                                  <div className="font-medium text-blue-800 mb-1">Input:</div>
                                  <div className="text-blue-700">{activity.input}</div>
                                </div>
                              )}
                              
                              {activity.output && (
                                <div className="bg-green-50 p-2 rounded text-xs">
                                  <div className="font-medium text-green-800 mb-1">Output:</div>
                                  <div className="text-green-700">{activity.output}</div>
                                </div>
                              )}
                              
                              {activity.error && (
                                <div className="bg-red-50 p-2 rounded text-xs">
                                  <div className="font-medium text-red-800 mb-1">Error:</div>
                                  <div className="text-red-700">{activity.error}</div>
                                </div>
                              )}
                              
                              {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                                <div className="bg-gray-50 p-2 rounded text-xs">
                                  <div className="font-medium text-gray-800 mb-1">Metadata:</div>
                                  <pre className="text-gray-700 whitespace-pre-wrap">
                                    {JSON.stringify(activity.metadata, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Summary */}
          {processData.activities.length > 0 && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="flex items-center justify-between text-sm">
                <div className="text-gray-600">
                  Process Summary: {completedActivities} of {totalActivities} steps completed
                </div>
                <div className="text-gray-500">
                  {processData.processingTime ? 
                    `Total: ${processData.processingTime.toFixed(1)}s` :
                    `Started: ${formatTime(processData.startTime)}`
                  }
                </div>
              </div>
              
              {progressPercentage > 0 && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progressPercentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};