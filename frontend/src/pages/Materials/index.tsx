/**
 * 资料库页面
 */

import { useEffect, useState } from 'react';
import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Button,
  Alert,
  Spin,
  message,
  Divider,
  Row,
  Col,
} from 'antd';
import {
  DownloadOutlined,
  BookOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { materialApi } from '../../api';
import type { Material } from '../../types';

const { Title, Text, Paragraph } = Typography;

export default function Materials() {
  const [loading, setLoading] = useState(false);
  const [materials, setMaterials] = useState<Material[]>([]);

  useEffect(() => {
    fetchMaterials();
  }, []);

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const categories = await materialApi.getCategories();
      // 获取所有类别的资料
      const allMaterials: Material[] = [];
      for (const category of categories) {
        const categoryMaterials = await materialApi.getMaterialsByCategory(category);
        allMaterials.push(...categoryMaterials);
      }
      setMaterials(allMaterials);
    } catch (error) {
      message.error('加载资料失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (material: Material) => {
    try {
      await materialApi.recordDownload(material.id);
      // 复制百度网盘链接到剪贴板
      navigator.clipboard.writeText(
        `链接：${material.baidu_link}\n提取码：${material.extract_code}`
      );
      message.success('链接和提取码已复制到剪贴板！');
      
      // 打开百度网盘链接
      window.open(material.baidu_link, '_blank');
      
      // 刷新数据以更新下载次数
      fetchMaterials();
    } catch (error) {
      message.error('记录下载失败');
    }
  };

  const getCategoryColor = (category: string) => {
    if (category.includes('high_school')) return 'blue';
    if (category.includes('university')) return 'green';
    return 'default';
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      high_school_comprehensive: '高中数学联赛综合',
      university_comprehensive: '大学数学竞赛综合',
      high_school_algebra: '高中-代数',
      high_school_geometry: '高中-几何',
      high_school_number_theory: '高中-数论',
      high_school_combinatorics: '高中-组合',
      university_algebra: '大学-代数',
      university_number_theory: '大学-数论',
      university_analysis: '大学-分析和方程',
      university_combinatorics: '大学-组合和概率',
      university_geometry: '大学-几何和拓扑',
      university_optimization: '大学-最优化方法',
    };
    return labels[category] || category;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>
        <BookOutlined /> 资料库
      </Title>

      {/* 使用说明 */}
      <Alert
        message="使用说明"
        description={
          <Space direction="vertical" size="small">
            <Text>1. 点击"下载"按钮，系统会自动复制百度网盘链接和提取码到剪贴板</Text>
            <Text>2. 浏览器会自动打开百度网盘链接，粘贴提取码即可下载</Text>
            <Text>3. 建议下载后先浏览资料，选择适合的题目作为母题</Text>
            <Text strong type="warning">
              ⚠️ 注意：只需要有明确答案的解答题，不要证明题、判断题或选择题
            </Text>
          </Space>
        }
        type="info"
        icon={<InfoCircleOutlined />}
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">资料类别</Text>
              <Title level={3} style={{ margin: '8px 0' }}>
                {materials.length}
              </Title>
              <Text type="secondary">个</Text>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">总下载次数</Text>
              <Title level={3} style={{ margin: '8px 0' }}>
                {materials.reduce((sum, m) => sum + m.download_count, 0)}
              </Title>
              <Text type="secondary">次</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 资料列表 */}
      <List
        grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
        dataSource={materials}
        renderItem={(material) => (
          <List.Item>
            <Card
              hoverable
              actions={[
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(material)}
                >
                  下载资料
                </Button>,
              ]}
            >
              <Card.Meta
                avatar={<BookOutlined style={{ fontSize: 32, color: '#1890ff' }} />}
                title={
                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <Text strong>{material.title}</Text>
                    <Tag color={getCategoryColor(material.category)}>
                      {getCategoryLabel(material.category)}
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Paragraph
                      ellipsis={{ rows: 2, expandable: true }}
                      style={{ marginBottom: 0 }}
                    >
                      {material.description}
                    </Paragraph>
                    <Divider style={{ margin: '8px 0' }} />
                    <Text type="secondary">
                      <DownloadOutlined /> {material.download_count} 次下载
                    </Text>
                  </Space>
                }
              />
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
}

