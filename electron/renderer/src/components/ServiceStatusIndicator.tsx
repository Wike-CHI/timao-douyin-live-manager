import React, { useState, useEffect } from 'react';
import { apiConfig } from '../services/apiConfig';

interface ServiceStatus {
  name: string;
  status: boolean;
  url: string;
}

export const ServiceStatusIndicator: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // 初始化服务状态
    const config = apiConfig.getConfig();
    const initialServices: ServiceStatus[] = Object.entries(config.services).map(([key, service]) => ({
      name: service.name,
      status: false,
      url: service.baseUrl
    }));
    setServices(initialServices);

    // 监听服务状态变化
    const handleStatusChange = (statusMap: Map<string, boolean>) => {
      setServices(prev => prev.map(service => {
        const serviceKey = Object.keys(config.services).find(
          key => config.services[key as keyof typeof config.services].name === service.name
        );
        return {
          ...service,
          status: serviceKey ? statusMap.get(serviceKey) || false : false
        };
      }));
    };

    apiConfig.addStatusListener(handleStatusChange);

    // 组件卸载时移除监听器
    return () => {
      apiConfig.removeStatusListener(handleStatusChange);
    };
  }, []);

  const allServicesHealthy = services.every(service => service.status);
  const anyServiceUnhealthy = services.some(service => !service.status);

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        {/* 状态指示器头部 */}
        <div 
          className="flex items-center gap-2 p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 rounded-t-lg"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className={`w-3 h-3 rounded-full ${
            allServicesHealthy 
              ? 'bg-green-500' 
              : anyServiceUnhealthy 
                ? 'bg-red-500' 
                : 'bg-yellow-500'
          }`} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            服务状态
          </span>
          <svg 
            className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        {/* 展开的服务详情 */}
        {isExpanded && (
          <div className="border-t border-gray-200 dark:border-gray-600">
            {services.map((service, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    service.status ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {service.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded ${
                    service.status 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    {service.status ? '正常' : '异常'}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(service.url, '_blank');
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    title={`访问 ${service.name}`}
                  >
                    访问
                  </button>
                </div>
              </div>
            ))}
            
            {/* 刷新按钮 */}
            <div className="border-t border-gray-200 dark:border-gray-600 p-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  apiConfig.checkAllServicesHealth();
                }}
                className="w-full text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
              >
                刷新状态
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceStatusIndicator;