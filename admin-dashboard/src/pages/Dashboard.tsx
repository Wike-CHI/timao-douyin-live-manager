import { Card, CardContent, Typography, Grid, Box } from '@mui/material';

export const Dashboard = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        仪表板
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                总用户数
              </Typography>
              <Typography variant="h4">
                -
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                待处理支付
              </Typography>
              <Typography variant="h4">
                -
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                订阅套餐
              </Typography>
              <Typography variant="h4">
                -
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                在线用户
              </Typography>
              <Typography variant="h4">
                -
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          欢迎使用管理后台
        </Typography>
        <Typography variant="body1" color="text.secondary">
          请从左侧菜单选择要管理的模块。基础框架已搭建完成，各功能模块将在后续阶段实现。
        </Typography>
      </Box>
    </Box>
  );
};

