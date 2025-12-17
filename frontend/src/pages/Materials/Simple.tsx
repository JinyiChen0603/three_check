/**
 * 资料库页面（简化版 - 静态数据）
 */

import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Button,
  Alert,
  Row,
  Col,
} from 'antd';
import {
  BookOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

// 12个资料类别（静态数据）
const materials = [
  {
    id: 1,
    category: '高中数学联赛综合',
    title: '高中数学联赛综合资料',
    description: '包含历年高中数学联赛真题及详解，涵盖代数、几何、数论、组合等各个方面',
    baidu_link: 'https://pan.baidu.com/s/example1',
    extract_code: 'abcd',
    download_count: 0,
  },
  {
    id: 2,
    category: '大学数学竞赛综合',
    title: '大学数学竞赛综合资料',
    description: '大学生数学竞赛历年真题合集，包含高等数学、线性代数、概率论等内容',
    baidu_link: 'https://pan.baidu.com/s/example2',
    extract_code: 'efgh',
    download_count: 0,
  },
  {
    id: 3,
    category: '高中数学联赛-代数',
    title: '高中联赛代数专题',
    description: '代数专项训练题库，包括多项式、不等式、函数等',
    baidu_link: 'https://pan.baidu.com/s/example3',
    extract_code: 'ijkl',
    download_count: 0,
  },
  {
    id: 4,
    category: '高中数学联赛-几何',
    title: '高中联赛几何专题',
    description: '平面几何、立体几何专项训练',
    baidu_link: 'https://pan.baidu.com/s/example4',
    extract_code: 'mnop',
    download_count: 0,
  },
  {
    id: 5,
    category: '高中数学联赛-数论',
    title: '高中联赛数论专题',
    description: '整除、同余、质数等数论问题',
    baidu_link: 'https://pan.baidu.com/s/example5',
    extract_code: 'qrst',
    download_count: 0,
  },
  {
    id: 6,
    category: '高中数学联赛-组合',
    title: '高中联赛组合专题',
    description: '排列组合、计数原理等组合数学问题',
    baidu_link: 'https://pan.baidu.com/s/example6',
    extract_code: 'uvwx',
    download_count: 0,
  },
  {
    id: 7,
    category: '大学数学竞赛-代数',
    title: '大学竞赛代数专题',
    description: '高等代数、线性代数专项训练',
    baidu_link: 'https://pan.baidu.com/s/example7',
    extract_code: 'yzab',
    download_count: 0,
  },
  {
    id: 8,
    category: '大学数学竞赛-数论',
    title: '大学竞赛数论专题',
    description: '初等数论、解析数论问题',
    baidu_link: 'https://pan.baidu.com/s/example8',
    extract_code: 'cdef',
    download_count: 0,
  },
  {
    id: 9,
    category: '大学数学竞赛-分析和方程',
    title: '大学竞赛分析与方程',
    description: '数学分析、微分方程专题',
    baidu_link: 'https://pan.baidu.com/s/example9',
    extract_code: 'ghij',
    download_count: 0,
  },
  {
    id: 10,
    category: '大学数学竞赛-组合和概率',
    title: '大学竞赛组合与概率',
    description: '组合数学、概率论与数理统计',
    baidu_link: 'https://pan.baidu.com/s/example10',
    extract_code: 'klmn',
    download_count: 0,
  },
  {
    id: 11,
    category: '大学数学竞赛-几何和拓扑',
    title: '大学竞赛几何与拓扑',
    description: '解析几何、拓扑学基础',
    baidu_link: 'https://pan.baidu.com/s/example11',
    extract_code: 'opqr',
    download_count: 0,
  },
  {
    id: 12,
    category: '大学数学竞赛-最优化方法',
    title: '大学竞赛最优化方法',
    description: '最优化理论与算法',
    baidu_link: 'https://pan.baidu.com/s/example12',
    extract_code: 'stuv',
    download_count: 0,
  },
];

export default function MaterialsSimple() {
  const handleDownload = (material: any) => {
    // 复制百度网盘链接到剪贴板
    const text = `链接：${material.baidu_link}\n提取码：${material.extract_code}`;
    navigator.clipboard.writeText(text);
    
    // 打开百度网盘链接
    window.open(material.baidu_link, '_blank');
  };

  const getCategoryColor = (category: string) => {
    if (category.includes('高中')) return 'blue';
    if (category.includes('大学')) return 'green';
    return 'default';
  };

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
                      {material.category}
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ marginBottom: 0 }}
                    >
                      {material.description}
                    </Paragraph>
                    <div>
                      <Text type="secondary">
                        📥 {material.download_count} 次下载
                      </Text>
                    </div>
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

