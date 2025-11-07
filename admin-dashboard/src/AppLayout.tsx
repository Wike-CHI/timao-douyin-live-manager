import { Layout, MenuItemLink, useSidebarState } from 'react-admin';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import PaymentIcon from '@mui/icons-material/Payment';
import CardMembershipIcon from '@mui/icons-material/CardMembership';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import BarChartIcon from '@mui/icons-material/BarChart';
import SecurityIcon from '@mui/icons-material/Security';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import RouterIcon from '@mui/icons-material/Router';

const CustomMenu = () => {
  useSidebarState();
  
  return (
    <div>
      <MenuItemLink
        to="/"
        primaryText="仪表板"
        leftIcon={<DashboardIcon />}
      />
      <MenuItemLink
        to="/users"
        primaryText="用户管理"
        leftIcon={<PeopleIcon />}
      />
      <MenuItemLink
        to="/payments"
        primaryText="支付管理"
        leftIcon={<PaymentIcon />}
      />
      <MenuItemLink
        to="/plans"
        primaryText="订阅套餐"
        leftIcon={<CardMembershipIcon />}
      />
      <MenuItemLink
        to="/ai-monitoring"
        primaryText="AI监控"
        leftIcon={<MonitorHeartIcon />}
      />
      <MenuItemLink
        to="/ai-gateway/providers"
        primaryText="AI网关 - 服务商"
        leftIcon={<RouterIcon />}
      />
      <MenuItemLink
        to="/ai-gateway/functions"
        primaryText="AI网关 - 功能配置"
        leftIcon={<RouterIcon />}
      />
      <MenuItemLink
        to="/analytics"
        primaryText="数据分析"
        leftIcon={<BarChartIcon />}
      />
      <MenuItemLink
        to="/system-monitor"
        primaryText="系统监控"
        leftIcon={<HealthAndSafetyIcon />}
      />
      <MenuItemLink
        to="/audit-logs"
        primaryText="审计日志"
        leftIcon={<SecurityIcon />}
      />
    </div>
  );
};

export const AppLayout = (props: any) => <Layout {...props} menu={CustomMenu} />;

