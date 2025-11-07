import {
  Show,
  TabbedShowLayout,
  Tab,
  TextField,
  NumberField,
  BooleanField,
  DateField,
  FunctionField,
} from 'react-admin';
import { Chip, Typography, Paper, Grid, Box } from '@mui/material';

const PlanTypeField = ({ record }: any) => {
  const typeMap: Record<string, { label: string; color: string }> = {
    free: { label: '免费', color: 'default' },
    basic: { label: '基础', color: 'primary' },
    professional: { label: '专业', color: 'success' },
    enterprise: { label: '企业', color: 'error' },
  };

  const type = record?.plan_type || 'free';
  const typeInfo = typeMap[type] || typeMap['free'];

  return <Chip label={typeInfo.label} color={typeInfo.color as any} />;
};

export const PlanShow = () => {
  return (
    <Show>
      <TabbedShowLayout>
        <Tab label="基本信息">
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  套餐信息
                </Typography>
                <TextField source="id" label="ID" />
                <TextField source="name" label="套餐名称" />
                <FunctionField
                  label="套餐类型"
                  render={(record: any) => <PlanTypeField record={record} />}
                />
                <TextField source="description" label="描述" />
                <BooleanField source="is_active" label="启用状态" />
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  价格信息
                </Typography>
                <NumberField
                  source="price"
                  label="价格"
                  options={{ style: 'currency', currency: 'CNY' }}
                />
                <NumberField
                  source="original_price"
                  label="原价"
                  options={{ style: 'currency', currency: 'CNY' }}
                />
                <FunctionField
                  label="计费周期"
                  render={(record: any) => {
                    const cycleMap: Record<string, string> = {
                      monthly: '月付',
                      quarterly: '季付',
                      yearly: '年付',
                      lifetime: '终身',
                    };
                    return <>{cycleMap[record?.billing_cycle] || record?.billing_cycle}</>;
                  }}
                />
                <NumberField source="duration_days" label="有效天数" />
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  配额设置
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      AI配额
                    </Typography>
                    <NumberField source="ai_quota" />
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      录制时长(分钟)
                    </Typography>
                    <NumberField source="recording_duration" />
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      存储空间(GB)
                    </Typography>
                    <NumberField source="storage_quota" />
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="textSecondary">
                      并发直播数
                    </Typography>
                    <NumberField source="max_concurrent_streams" />
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        </Tab>

        <Tab label="功能权限">
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  核心功能
                </Typography>
                <BooleanField source="features.live_recording" label="直播录制" />
                <BooleanField source="features.ai_analysis" label="AI分析" />
                <BooleanField source="features.multi_platform" label="多平台支持" />
                <BooleanField source="features.real_time_transcription" label="实时转写" />
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  高级功能
                </Typography>
                <BooleanField source="features.advanced_analytics" label="高级分析" />
                <BooleanField source="features.custom_branding" label="自定义品牌" />
                <BooleanField source="features.api_access" label="API访问" />
                <BooleanField source="features.priority_support" label="优先支持" />
              </Paper>
            </Grid>
          </Grid>
        </Tab>

        <Tab label="时间信息">
          <DateField source="created_at" label="创建时间" showTime />
          <DateField source="updated_at" label="更新时间" showTime />
          <FunctionField
            label="订阅统计"
            render={(record: any) => {
              return (
                <Box sx={{ mt: 2 }}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1">
                      当前订阅数: {record?.subscription_count || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      活跃订阅: {record?.active_subscriptions || 0}
                    </Typography>
                  </Paper>
                </Box>
              );
            }}
          />
        </Tab>
      </TabbedShowLayout>
    </Show>
  );
};
