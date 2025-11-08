import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Box,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Typography,
  CircularProgress,
} from '@mui/material';
import { Title } from 'react-admin';

interface AuditLog {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  level: string;
  category: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  details?: any;
}

export const AuditLogs: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    fetchLogs();
  }, [page, rowsPerPage, searchTerm, levelFilter, categoryFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:15000';

      const params = new URLSearchParams({
        limit: rowsPerPage.toString(),
        skip: (page * rowsPerPage).toString(),
      });

      if (searchTerm) params.append('search', searchTerm);
      if (levelFilter !== 'all') params.append('level', levelFilter);
      if (categoryFilter !== 'all') params.append('category', categoryFilter);

      const response = await fetch(`${baseUrl}/api/admin/activities/recent?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(Array.isArray(data) ? data : []);
        setTotal(data.length || 0);
      }
    } catch (error) {
      console.error('获取审计日志失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'info': return 'info';
      case 'warning': return 'warning';
      case 'error': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'auth': return 'primary';
      case 'user': return 'info';
      case 'payment': return 'success';
      case 'subscription': return 'secondary';
      case 'system': return 'warning';
      default: return 'default';
    }
  };

  if (loading && logs.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Title title="审计日志" />
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          审计日志查询
        </Typography>
        
        <Box display="flex" gap={2} flexWrap="wrap">
          <TextField
            label="搜索"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索操作、资源..."
            sx={{ minWidth: 200 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>级别</InputLabel>
            <Select
              value={levelFilter}
              label="级别"
              onChange={(e) => setLevelFilter(e.target.value)}
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="info">Info</MenuItem>
              <MenuItem value="warning">Warning</MenuItem>
              <MenuItem value="error">Error</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>类别</InputLabel>
            <Select
              value={categoryFilter}
              label="类别"
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="all">全部</MenuItem>
              <MenuItem value="auth">认证</MenuItem>
              <MenuItem value="user">用户</MenuItem>
              <MenuItem value="payment">支付</MenuItem>
              <MenuItem value="subscription">订阅</MenuItem>
              <MenuItem value="system">系统</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>时间</TableCell>
                <TableCell>用户ID</TableCell>
                <TableCell>操作</TableCell>
                <TableCell>资源类型</TableCell>
                <TableCell>资源ID</TableCell>
                <TableCell>级别</TableCell>
                <TableCell>类别</TableCell>
                <TableCell>IP地址</TableCell>
                <TableCell>详情</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} hover>
                  <TableCell>{log.id}</TableCell>
                  <TableCell>
                    {new Date(log.created_at).toLocaleString('zh-CN')}
                  </TableCell>
                  <TableCell>{log.user_id || '-'}</TableCell>
                  <TableCell>
                    <strong>{log.action}</strong>
                  </TableCell>
                  <TableCell>
                    <Chip label={log.resource_type} size="small" />
                  </TableCell>
                  <TableCell>{log.resource_id || '-'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={log.level} 
                      color={getLevelColor(log.level)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={log.category} 
                      color={getCategoryColor(log.category)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                      {log.ip_address || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {log.details ? (
                      <Typography variant="caption" sx={{ maxWidth: 200, display: 'block' }}>
                        {JSON.stringify(log.details).substring(0, 50)}...
                      </Typography>
                    ) : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="每页行数:"
        />
      </Paper>
    </div>
  );
};
