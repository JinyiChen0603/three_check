/**
 * 资料库页面
 */

import { useEffect, useState, useMemo } from 'react';
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
  Checkbox,
  Empty,
} from 'antd';
import {
  DownloadOutlined,
  BookOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { materialApi, type CategorySummary, type MaterialResponse } from '../../api';

const { Title, Text, Paragraph } = Typography;

// 大类别定义
const MAIN_CATEGORIES = [
  { key: 'high_school', label: '高中数学联赛', prefix: 'high_school' },
  { key: 'college', label: '大学数学竞赛', prefix: 'college' },
];

export default function Materials() {
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [allMaterials, setAllMaterials] = useState<MaterialResponse[]>([]);
  // 选中的大类别
  const [selectedMainCategories, setSelectedMainCategories] = useState<string[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 获取类别汇总
      const categoriesData = await materialApi.getCategories();
      setCategories(categoriesData);
      // 获取所有资料
      const materialsData = await materialApi.getMaterials();
      setAllMaterials(materialsData);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载资料失败');
    } finally {
      setLoading(false);
    }
  };

  // 根据选中的大类别筛选资料
  const materials = useMemo(() => {
    if (selectedMainCategories.length === 0) {
      return allMaterials;
    }
    return allMaterials.filter((m) => 
      selectedMainCategories.some((prefix) => m.category.startsWith(prefix))
    );
  }, [allMaterials, selectedMainCategories]);

  // 切换大类别选中状态
  const toggleMainCategory = (prefix: string) => {
    setSelectedMainCategories((prev) => {
      if (prev.includes(prefix)) {
        return prev.filter((p) => p !== prefix);
      }
      return [...prev, prefix];
    });
  };

  const handleDownload = async (material: MaterialResponse) => {
    try {
      await materialApi.recordDownload(material.id);
      // 复制百度网盘链接到剪贴板
      const extractCodeText = material.extract_code ? `\n提取码：${material.extract_code}` : '';
      navigator.clipboard.writeText(
        `链接：${material.baidu_link}${extractCodeText}`
      );
      message.success('链接和提取码已复制到剪贴板！');
      
      // 打开百度网盘链接
      window.open(material.baidu_link, '_blank');
      
      // 刷新数据以更新下载次数
      fetchData();
    } catch (error) {
      message.error('记录下载失败');
    }
  };

  const getCategoryColor = (category: string) => {
    if (category.includes('high_school')) return 'blue';
    if (category.includes('college')) return 'green';
    return 'default';
  };

  // 计算统计数据
  const totalMaterials = categories.reduce((sum, c) => sum + c.material_count, 0);
  const totalDownloads = categories.reduce((sum, c) => sum + c.total_downloads, 0);

  if (loading && materials.length === 0) {
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
        title="使用说明"
        description={
          <div>
            <p>1. 点击"下载"按钮，系统会自动复制百度网盘链接和提取码到剪贴板</p>
            <p>2. 浏览器会自动打开百度网盘链接，粘贴提取码即可下载</p>
            <p>3. 建议下载后先浏览资料，选择适合的题目作为母题</p>
            <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
              ⚠️ 注意：只需要有明确答案的解答题，不要证明题、判断题或选择题
            </p>
          </div>
        }
        type="info"
        icon={<InfoCircleOutlined />}
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">资料类别</Text>
              <Title level={3} style={{ margin: '8px 0' }}>
                {categories.length}
              </Title>
              <Text type="secondary">个</Text>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">资料总数</Text>
              <Title level={3} style={{ margin: '8px 0' }}>
                {totalMaterials}
              </Title>
              <Text type="secondary">个</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">总下载次数</Text>
              <Title level={3} style={{ margin: '8px 0' }}>
                {totalDownloads}
              </Title>
              <Text type="secondary">次</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 筛选器 */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large" wrap>
          <Text strong>筛选类别：</Text>
          {MAIN_CATEGORIES.map((cat) => {
            // 计算该大类别下的资料数量
            const count = allMaterials.filter((m) => m.category.startsWith(cat.prefix)).length;
            return (
              <Checkbox
                key={cat.key}
                checked={selectedMainCategories.includes(cat.prefix)}
                onChange={() => toggleMainCategory(cat.prefix)}
              >
                {cat.label} ({count})
              </Checkbox>
            );
          })}
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchData}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 资料列表 */}
      {materials.length === 0 ? (
        <Card>
          <Empty description="暂无资料" />
        </Card>
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }}
          dataSource={materials}
          loading={loading}
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
                    <div>
                      <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        {material.title}
                      </Text>
                      <Tag color={getCategoryColor(material.category)}>
                        {material.category_display}
                      </Tag>
                    </div>
                  }
                  description={
                    <div>
                      <Paragraph
                        ellipsis={{ rows: 2, expandable: true }}
                        style={{ marginBottom: 8 }}
                      >
                        {material.description || '暂无描述'}
                      </Paragraph>
                      <Divider style={{ margin: '8px 0' }} />
                      <Text type="secondary">
                        <DownloadOutlined /> {material.download_count} 次下载
                      </Text>
                    </div>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

