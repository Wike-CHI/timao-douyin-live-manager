import { Layout, MenuItemLink, useSidebarState } from 'react-admin';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import PaymentIcon from '@mui/icons-material/Payment';
import CardMembershipIcon from '@mui/icons-material/CardMembership';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import OnlinePredictionIcon from '@mui/icons-material/OnlinePrediction';
import SettingsIcon from '@mui/icons-material/Settings';

const CustomMenu = () => {
  const [open] = useSidebarState();
  
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
        to="/online-users"
        primaryText="在线用户"
        leftIcon={<OnlinePredictionIcon />}
      />
      <MenuItemLink
        to="/revenue"
        primaryText="流水统计"
        leftIcon={<TrendingUpIcon />}
      />
      <MenuItemLink
        to="/ai-gateway"
        primaryText="AI网关"
        leftIcon={<SettingsIcon />}
      />
    </div>
  );
};

export const AppLayout = (props: any) => <Layout {...props} menu={CustomMenu} />;

