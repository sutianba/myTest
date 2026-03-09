#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""SQLite数据库配置（替代MySQL）"""

import os
import sqlite3
from contextlib import contextmanager

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flower_recognition.db')

def get_db_connection():
    """获取SQLite数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """上下文管理器获取数据库连接"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_sqlite_db():
    """初始化SQLite数据库"""
    try:
        print("正在初始化SQLite数据库...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建识别结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recognition_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                image_path TEXT,
                result TEXT,
                confidence REAL,
                corrected INTEGER DEFAULT 0,
                original_result TEXT,
                corrected_at TIMESTAMP,
                renamed INTEGER DEFAULT 0,
                renamed_at TIMESTAMP,
                image_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 创建反馈表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recognition_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER,
                user_id INTEGER,
                feedback_type TEXT DEFAULT 'wrong',
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (result_id) REFERENCES recognition_results(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 创建植物信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                scientific_name TEXT NOT NULL,
                category TEXT NOT NULL,
                family TEXT,
                description TEXT,
                image_url TEXT,
                blooming_season TEXT,
                growth_stage TEXT,
                sunlight_requirements TEXT,
                water_needs TEXT,
                origin TEXT,
                toxicity TEXT,
                care_tips TEXT,
                planting_instructions TEXT,
                propagation_methods TEXT,
                pests_and_diseases TEXT,
                similar_plants TEXT,
                benefits TEXT,
                other_names TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # 插入基础植物数据
        plants_data = [
            {
                'name': '玫瑰',
                'scientific_name': 'Rosa',
                'category': '花卉',
                'family': '蔷薇科',
                'description': '玫瑰是一种象征爱情与美丽的花卉，拥有丰富的花色和浓郁的香气。在世界各地广泛栽培，是最受欢迎的观赏花卉之一。',
                'image_url': 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Beautiful%20rose%20flower%2C%20garden&sign=25015e95c4b359ce0e75c1b8c4e55e4b',
                'blooming_season': '夏季至秋季',
                'growth_stage': '春季发芽，夏季开花，秋季结果，冬季休眠',
                'sunlight_requirements': '充足阳光（每天至少6小时）',
                'water_needs': '中等（保持土壤湿润但不过湿）',
                'origin': '欧洲、亚洲、中东',
                'toxicity': '轻微（刺可能引起皮肤刺激）',
                'care_tips': '保持土壤湿润但不过湿，定期施肥。避免叶片沾水，以防真菌病害。',
                'planting_instructions': '选择排水良好的肥沃土壤，种植在阳光充足的位置。种植前添加有机肥料。',
                'propagation_methods': '可以通过扦插、嫁接或分株繁殖。扦插最好在春季或夏季进行。',
                'pests_and_diseases': '常见病虫害有蚜虫、红蜘蛛和白粉病。定期检查并及时防治。',
                'similar_plants': '月季：花型相似但花期更长；蔷薇：攀缘性更强，花小而多',
                'benefits': '花朵可用于制作香料、精油和花茶，具有舒缓情绪、促进血液循环的功效。',
                'other_names': '玫瑰花,月季'
            },
            {
                'name': '郁金香',
                'scientific_name': 'Tulipa',
                'category': '花卉',
                'family': '百合科',
                'description': '郁金香是春季开花的球根花卉，花色艳丽，花形端庄，是荷兰的国花。已有数百年的栽培历史，品种繁多。',
                'image_url': 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Colorful%20tulip%20flowers%2C%20garden&sign=0696ea8d7f0693e3fd18827500f7700a',
                'blooming_season': '春季',
                'growth_stage': '秋季种植，冬季休眠，春季开花，夏季枯萎',
                'sunlight_requirements': '充足阳光（每天至少5小时）',
                'water_needs': '中等（生长期保持湿润，休眠期减少浇水）',
                'origin': '土耳其、中亚',
                'toxicity': '轻微（可能引起胃部不适）',
                'care_tips': '种植在排水良好的土壤中，花后继续养护至叶片枯萎。秋季种植球茎最佳。',
                'planting_instructions': '秋季将球茎种植在排水良好的土壤中，深度约为球茎直径的2-3倍。',
                'propagation_methods': '主要通过分球繁殖，也可播种繁殖但需要较长时间才能开花。',
                'pests_and_diseases': '可能受到蚜虫、根腐病和灰霉病的影响。保持通风良好可减少病害发生。',
                'similar_plants': '风信子：花穗状，香气浓郁；水仙：花形不同，多为黄色',
                'benefits': '是重要的春季观赏花卉，常用于花坛、切花和盆栽观赏。',
                'other_names': '洋荷花,草麝香'
            },
            {
                'name': '薰衣草',
                'scientific_name': 'Lavandula',
                'category': '花卉',
                'family': '唇形科',
                'description': '薰衣草是一种芳香植物，以其紫色的花朵和独特的香气而闻名。主要用于香料、药用和观赏。',
                'image_url': 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Lavender%20field%2C%20purple%20flowers&sign=18ec56878cd00dafb53d98d7474ef2d4',
                'blooming_season': '夏季',
                'growth_stage': '春季生长，夏季开花，秋季结籽，冬季休眠',
                'sunlight_requirements': '充足阳光（每天至少6-8小时）',
                'water_needs': '低（耐旱，避免过度浇水）',
                'origin': '地中海地区',
                'toxicity': '无（但过量使用精油可能引起不适）',
                'care_tips': '种植在干燥、排水良好的土壤中，避免过度浇水。开花后修剪促进新枝生长。',
                'planting_instructions': '选择排水良好的沙质土壤，种植在阳光充足的位置。避免土壤过于湿润。',
                'propagation_methods': '可以通过扦插、分株或播种繁殖。扦插繁殖最常用且成功率高。',
                'pests_and_diseases': '较少受到病虫害影响。可能的问题包括根腐病（由于土壤过湿）和蚜虫。',
                'similar_plants': '迷迭香：叶片针状，香气不同；薄荷：叶片较大，生长更旺盛',
                'benefits': '具有镇静、抗菌和抗炎作用。常用于制作香水、香薰、护肤品和草药茶。',
                'other_names': '灵香草,黄香草'
            },
            {
                'name': '仙人掌',
                'scientific_name': 'Cactaceae',
                'category': '多肉',
                'family': '仙人掌科',
                'description': '仙人掌是一类适应干旱环境的多肉植物，形态各异，易于养护。原产于美洲，现广泛栽培作为观赏植物。',
                'image_url': 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Cactus%20plant%2C%20desert&sign=21bd44f25b466835546afac78d000ba0',
                'blooming_season': '春季至夏季（部分品种）',
                'growth_stage': '全年生长缓慢，冬季休眠',
                'sunlight_requirements': '充足阳光（每天至少4-6小时）',
                'water_needs': '很低（生长期适度浇水，休眠期几乎不浇水）',
                'origin': '美洲',
                'toxicity': '大多数无',
                'care_tips': '极少浇水，避免积水，冬季减少浇水频率。使用排水良好的多肉植物专用土。',
                'planting_instructions': '使用排水良好的多肉植物专用土壤，种植在阳光充足的位置。花盆底部可添加碎石增加排水性。',
                'propagation_methods': '可以通过扦插、分株或播种繁殖。许多种类可以通过单个茎段繁殖。',
                'pests_and_diseases': '常见问题有红蜘蛛、粉蚧和根腐病（由于浇水过多）。',
                'similar_plants': '仙人球：球形，刺密集；多肉植物：形态多样，刺较少',
                'benefits': '作为室内观赏植物可以净化空气，减少空气中的污染物。',
                'other_names': '仙人球,刺球'
            },
            {
                'name': '绿萝',
                'scientific_name': 'Epipremnum aureum',
                'category': '藤蔓',
                'family': '天南星科',
                'description': '绿萝是一种常见的室内观叶植物，生长迅速，易于养护。因其心形叶片和藤蔓生长习性而受欢迎。',
                'image_url': 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Pothos%20plant%2C%20indoor%20green&sign=80cca437f333913280f156947d70cc9f',
                'blooming_season': '极少开花（室内几乎不开花）',
                'growth_stage': '全年生长，夏季生长旺盛',
                'sunlight_requirements': '散射光（避免阳光直射）',
                'water_needs': '中等（待土壤表面干燥后再浇水）',
                'origin': '所罗门群岛',
                'toxicity': '轻微（对宠物）',
                'care_tips': '保持土壤湿润但不过湿，避免阳光直射。定期擦拭叶片保持清洁。',
                'planting_instructions': '选择排水良好的土壤，种植在散射光充足的位置。可以垂吊或攀爬生长。',
                'propagation_methods': '可以通过扦插繁殖，将茎段插入水中或土壤中即可生根。',
                'pests_and_diseases': '可能受到蚜虫、介壳虫和根腐病的影响。保持通风良好可减少病虫害。',
                'similar_plants': '常春藤：叶片较小，攀缘能力强；龟背竹：叶片孔洞状',
                'benefits': '可以净化室内空气，吸收甲醛等有害物质。',
                'other_names': '黄金葛,魔鬼藤'
            }
        ]
        
        # 插入植物数据
        for plant in plants_data:
            cursor.execute("SELECT id FROM plants WHERE name = ?", (plant['name'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO plants (
                        name, scientific_name, category, family, description, image_url,
                        blooming_season, growth_stage, sunlight_requirements, water_needs,
                        origin, toxicity, care_tips, planting_instructions, propagation_methods,
                        pests_and_diseases, similar_plants, benefits, other_names
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plant['name'], plant['scientific_name'], plant['category'], plant['family'], plant['description'],
                    plant['image_url'], plant['blooming_season'], plant['growth_stage'], plant['sunlight_requirements'],
                    plant['water_needs'], plant['origin'], plant['toxicity'], plant['care_tips'],
                    plant['planting_instructions'], plant['propagation_methods'], plant['pests_and_diseases'],
                    plant['similar_plants'], plant['benefits'], plant['other_names']
                ))
                print(f"  - 插入植物: {plant['name']}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\nSQLite数据库初始化完成！")
        print(f"数据库文件: {DB_PATH}")
        
    except Exception as e:
        print(f"数据库初始化失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_sqlite_db()
