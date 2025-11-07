import {
  Edit,
  SimpleForm,
  TextInput,
  NumberInput,
  SelectInput,
  BooleanInput,
  required,
  minValue,
} from 'react-admin';
import { Grid } from '@mui/material';

const planTypeChoices = [
  { id: 'free', name: '免费' },
  { id: 'basic', name: '基础' },
  { id: 'professional', name: '专业' },
  { id: 'enterprise', name: '企业' },
];

const billingCycleChoices = [
  { id: 'monthly', name: '月付' },
  { id: 'quarterly', name: '季付' },
  { id: 'yearly', name: '年付' },
  { id: 'lifetime', name: '终身' },
];

export const PlanEdit = () => {
  return (
    <Edit>
      <SimpleForm>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextInput
              source="name"
              label="套餐名称"
              validate={required()}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <SelectInput
              source="plan_type"
              label="套餐类型"
              choices={planTypeChoices}
              validate={required()}
              fullWidth
            />
          </Grid>

          <Grid item xs={12}>
            <TextInput
              source="description"
              label="描述"
              multiline
              rows={3}
              fullWidth
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <NumberInput
              source="price"
              label="价格"
              validate={[required(), minValue(0)]}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <NumberInput
              source="original_price"
              label="原价"
              validate={minValue(0)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <SelectInput
              source="billing_cycle"
              label="计费周期"
              choices={billingCycleChoices}
              validate={required()}
              fullWidth
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <NumberInput
              source="duration_days"
              label="有效天数"
              validate={[required(), minValue(1)]}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <NumberInput
              source="ai_quota"
              label="AI配额"
              validate={minValue(0)}
              fullWidth
              helperText="0表示无限制"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <NumberInput
              source="recording_duration"
              label="录制时长(分钟)"
              validate={minValue(0)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <NumberInput
              source="storage_quota"
              label="存储空间(GB)"
              validate={minValue(0)}
              fullWidth
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <NumberInput
              source="max_concurrent_streams"
              label="并发直播数"
              validate={minValue(1)}
              fullWidth
            />
          </Grid>

          <Grid item xs={12}>
            <BooleanInput source="is_active" label="启用套餐" />
          </Grid>
        </Grid>
      </SimpleForm>
    </Edit>
  );
};
