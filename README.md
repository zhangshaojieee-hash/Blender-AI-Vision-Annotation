# Blender AI Vision Annotation Helper

当前版本：`v0.4.0`

用于给 STL、OBJ、GLB/GLTF 三维模型做第一轮人工结构标注。插件记录物体类别、部件、关节候选、关节轴、置信度和模型指纹，输出 JSON 供后续几何算法和 AI 方向使用。

本插件只记录人工标注候选，不会自动生成磁场强度、线圈电流或 `MAG_ON/MAG_OFF` 设备命令。

## 1. 安装插件

1. 从 GitHub 下载 ZIP，或将 `blender_annotation_addon` 文件夹压缩为 `blender_annotation_addon.zip`。
2. 打开 Blender 4.x/5.x。
3. 进入 `Edit > Preferences > Add-ons`。
4. 点击右上角 `Install...`。
5. 选择 `blender_annotation_addon.zip`。
6. 搜索 `AI Vision Annotation Helper` 并勾选启用。
7. 回到 3D View，按 `N` 打开侧栏。
8. 选择 `AI Vision` 标签。

压缩包内部第一层必须直接包含：

```text
blender_annotation_addon/
  __init__.py
  annotation_data.py
  operators.py
  panel.py
  properties.py
```

### 更新旧版本

如果面板没有显示 `Marked parts` 和 `Marked joints`：

1. 在 Preferences 中搜索 `AI Vision`。
2. 取消勾选旧版本并点击 `Remove`（如果有）。
3. 完全关闭 Blender，包括所有窗口。
4. 重新打开 Blender。
5. 重新安装最新版 ZIP。

Blender 可能缓存旧的 Python 子模块，仅取消勾选再勾选不一定会刷新代码。

## 2. 第一次标注前的准备

### 2.1 保存 Blender 工程

先导入模型，再执行 `File > Save As`，例如保存为：

```text
model_01_张三.blend
```

保存后，插件会根据 `Object type` 自动输出到：

```text
<当前 blend 文件夹>/annotations/<object_type>.json
```

例如 `Object type` 填写 `two_link_leg`，输出文件就是 `annotations/two_link_leg.json`。这是跨电脑默认路径，不依赖任何人的 Windows 用户名。

### 2.2 填写 Project 区域

在 `AI Vision` 面板的 `Project` 中填写：

- `Object type`：物体类别，例如 `two_link_leg`、`arm`、`clip`；
- `Annotator`：标注人姓名或 GitHub 用户名；
- `Object confidence`：对整个物体类别判断的确定程度；
- `Source model`：原始 STL/OBJ/GLB 文件；
- `Output JSON`：由插件自动生成，通常不需要手动修改。

建议每个模型使用独立文件名，例如：

```text
annotations/obj_01_腿_张三.json
```

不要让不同模型或不同标注人的结果覆盖同一个 `annotation.json`。

## 3. 标注部件

### 3.1 一个部件对应一个 Blender 对象

当前插件按 Blender 对象记录部件，而不是按编辑模式中的局部面记录。

如果模型已经包含多个对象：

1. 在 Object Mode 选中部件对象；
2. 设置 `Annotation confidence`；
3. 点击 `Add selected as part`；
4. 检查列表中的 `Marked parts`。

如果一个 STL 是整体对象，但里面有多个杆件：

1. 进入 Edit Mode；
2. 选择第一个杆件的面；
3. 按 `P`；
4. 选择 `Selection` 分离；
5. 回到 Object Mode；
6. 重命名为 `link_a`；
7. 对第二个杆件重复，命名为 `link_b`；
8. 分别点击 `Add selected as part`。

### 3.2 检查部件列表

成功后面板应显示：

```text
Marked parts: 2
link_a confidence=0.70
link_b confidence=0.70
```

没有点击 `Add selected as part` 的对象不会进入 JSON 的 `parts`。

## 4. 标注关节

1. 选中与关节相连的部件，例如 `link_a` 和 `link_b`；
2. 将 3D 光标放到关节候选位置；
3. 在 `Joint type` 填写 `hinge_candidate`；
4. 选择候选旋转轴 X、Y 或 Z；
5. 设置 `Annotation confidence`；
6. 在备注中写不确定性，例如 `圆柱连接中心附近，轴线待机械复核`；
7. 点击 `Add joint at 3D cursor`。

3D 光标放置方式：

- `Shift + 右键`；
- 3D View 左侧工具栏中的 3D Cursor 工具。

成功后面板应显示：

```text
Marked joints: 1
joint_01 (...) c=0.70
```

如果同一位置已经有一个关节，插件会阻止重复创建。已有错误标注时使用 `Remove last joint`，或点击 `Clear annotation marks` 后重新标注。

## 5. 置信度填写规范

置信度是标注者对标签正确性的主观确定程度，不是模型预测概率。

| 情况 | 建议值 |
| --- | ---: |
| 类别和边界都非常清楚 | 0.90-0.98 |
| 基本确定，但边界或中心有误差 | 0.75-0.89 |
| 只有局部结构或大致位置 | 0.55-0.74 |
| 只是猜测 | 0.20-0.54 |

例如：只选择大腿一部分面，关节中心是目测位置，可使用 `0.60-0.70`，并在备注中说明原因。

即使置信度较高，`needs_human_review` 仍应保留为 `true`，因为这属于人工候选标注，不是经过几何、材料和硬件验证的最终方案。

## 6. 导出 JSON

点击 `Save annotation JSON`。插件会自动记录：

- 原始模型文件名和路径；
- 原始模型 SHA-256 指纹；
- Blender 工程路径（如果已保存）；
- 物体类别和置信度；
- 部件对象名称和置信度；
- 关节坐标、轴和关联部件；
- 标注人和 UTC 时间；
- 插件工具名称；
- 人工复核状态。

插件会在导出前检查：

- 是否填写标注人；
- 是否填写物体类别；
- 是否选择原始模型；
- 原始模型是否可以读取；
- 是否至少标注一个部件和一个关节。

缺少这些信息时，导出会被阻止并在 Blender 状态栏提示错误。

## 7. 导出前检查

```text
[ ] JSON 能正常打开
[ ] source_model 是原始 STL/OBJ/GLB
[ ] model_fingerprint 不为空
[ ] Annotator 不是空值
[ ] Object type 不是 unknown
[ ] parts 数量正确
[ ] joint_candidates 数量正确且没有重复
[ ] connected_parts 与实际部件一致
[ ] 坐标单位和坐标系已确认
[ ] needs_human_review 状态没有被误改
```

## 8. 当前限制

- 关节位置使用 Blender 场景坐标，必须确认场景缩放和单位；
- 关节轴目前只能选择 X、Y、Z 主轴；
- 部件以 Blender 对象为单位，局部面必须先分离对象；
- 插件不自动推断关节；
- 插件不生成磁化强度或设备控制命令；
- AI 候选必须经过人工确认、几何约束和硬件约束；
- 没有材料标定数据时，不得把候选写成真实设备参数。

## 9. 遇到问题时提交的信息

请在 GitHub Issue 或项目群中同时提供：

1. Blender 版本；
2. 插件版本；
3. 操作步骤；
4. Blender 状态栏或控制台报错；
5. 相关 JSON（删除敏感路径后）；
6. 是否使用了原始 STL/OBJ/GLB；
7. 截图或最小复现文件。
