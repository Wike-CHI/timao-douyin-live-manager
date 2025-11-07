import { Admin, Resource, CustomRoutes } from 'react-admin';
import { Route } from 'react-router-dom';
import { authProvider } from './authProvider';
import { dataProvider } from './dataProvider';
import { AppLayout } from './AppLayout';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { UserList, UserShow, UserCreate, UserEdit } from './resources/users';
import { PaymentList, PaymentShow } from './resources/payments';
import { PlanList, PlanShow, PlanCreate, PlanEdit } from './resources/plans';
import { AICostStats } from './resources/ai-monitoring';
import { RevenueCharts } from './resources/analytics/RevenueCharts';
import { SystemMonitor } from './resources/system/SystemMonitor';
import { AuditLogs } from './resources/audit/AuditLogs';
import { ProviderList, FunctionList } from './resources/ai-gateway';

function App() {
  return (
    <Admin
      authProvider={authProvider}
      dataProvider={dataProvider}
      layout={AppLayout}
      loginPage={LoginPage}
      dashboard={Dashboard}
      theme={{
        palette: {
          mode: 'light',
          primary: {
            main: '#1976d2',
          },
          secondary: {
            main: '#dc004e',
          },
        },
      }}
      title="提猫直播助手 - 管理后台"
    >
      <Resource
        name="users"
        list={UserList}
        show={UserShow}
        create={UserCreate}
        edit={UserEdit}
      />
      
      <Resource
        name="payments"
        list={PaymentList}
        show={PaymentShow}
      />
      
      <Resource
        name="plans"
        list={PlanList}
        show={PlanShow}
        create={PlanCreate}
        edit={PlanEdit}
      />
      
      <CustomRoutes>
        <Route path="/ai-monitoring" element={<AICostStats />} />
        <Route path="/analytics" element={<RevenueCharts />} />
        <Route path="/system-monitor" element={<SystemMonitor />} />
        <Route path="/audit-logs" element={<AuditLogs />} />
        <Route path="/ai-gateway/providers" element={<ProviderList />} />
        <Route path="/ai-gateway/functions" element={<FunctionList />} />
      </CustomRoutes>
    </Admin>
  );
}

export default App;

