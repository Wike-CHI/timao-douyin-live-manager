import { Admin, Resource } from 'react-admin';
import { authProvider } from './authProvider';
import { dataProvider } from './dataProvider';
import { AppLayout } from './AppLayout';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { UserList, UserShow, UserCreate, UserEdit } from './resources/users';

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
    </Admin>
  );
}

export default App;

