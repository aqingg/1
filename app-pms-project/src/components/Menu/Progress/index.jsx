import React, { useMemo, useState, useEffect, useCallback  } from 'react';
import { Typography, Tree, Space, message, Tooltip, Modal, Button } from 'antd';
import {
  CheckCircleOutlined,
  PauseCircleOutlined,
  MinusCircleOutlined,
  SyncOutlined,
  ProjectOutlined,
  CopyOutlined,
  DeleteOutlined,
} from '@ant-design/icons';

import ProgressBar from '../ProgressBar';
import { useAppContext } from "../../../context/AppContext";

const WINDOWS_CALIBRATION_ID_PATTERN = /[<>:"/\\|?*]/;

const uuid = () => crypto.randomUUID();

const collectSubtreeIds = (task, collected = []) => {
  if (!task) return collected;
  collected.push(task.id);
  task.children?.forEach((child) => collectSubtreeIds(child, collected));
  return collected;
};

const findNode = (nodes, id) => {
  for (const node of nodes) {
    if (node.id === id) return node;
    if (node.children?.length) {
      const result = findNode(node.children, id);
      if (result) return result;
    }
  }
  return null;
};

const findParentNode = (nodes, id, parent = null) => {
  for (const node of nodes) {
    if (node.id === id) return parent;
    if (node.children?.length) {
      const result = findParentNode(node.children, id, node);
      if (result) return result;
    }
  }
  return null;
};

const findParentAndIndex = (nodes, id, parent = null) => {
  for (let index = 0; index < nodes.length; index += 1) {
    const node = nodes[index];

    if (node.id === id) {
      return { parent, index, siblings: nodes };
    }

    if (node.children?.length) {
      const result = findParentAndIndex(node.children, id, node);
      if (result) return result;
    }
  }
  return null;
};

const hasControlCharacters = (value) =>
  Array.from(value || "").some((character) => character.charCodeAt(0) < 32);

const deepCopyTask = (task, newDetails, taskDetails) => {
  const newId = uuid();

  if (taskDetails?.[task.id]) {
    newDetails[newId] = {
      ...taskDetails[task.id],
      taskName: taskDetails[task.id].taskName + " (Copy)",
    };
  }

  return {
    ...task,
    id: newId,
    status: "Pending",
    children: task.children?.map((child) => deepCopyTask(child, newDetails, taskDetails)) || [],
  };
};

const deepCopyCalibrationSubtree = (task, newDetails, rootTaskName, taskDetails) => {
  const newId = uuid();
  const originalDetail = taskDetails?.[task.id];

  if (originalDetail) {
    newDetails[newId] = {
      ...structuredClone(originalDetail),
      taskName: rootTaskName,
    };
  } else {
    newDetails[newId] = { taskName: rootTaskName };
  }

  return {
    ...task,
    id: newId,
    taskName: rootTaskName,
    status: "Pending",
    children: task.children?.map((child) => deepCopyCalibrationSubtree(child, newDetails, child.taskName, taskDetails)) || [],
  };
};

const { Title, Text } = Typography;

export default function Progress() {
  const { projectWorkFlow, updateWorkFlow, user, projectName, projectId, createCalibrationWorkspace } =
    useAppContext();

  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const taskTree = useMemo(() => projectWorkFlow?.taskTree || [], [projectWorkFlow?.taskTree]);

  // ===========================
  // 状态图标
  // ===========================
  const getStatusIcon = (status) => {
    switch (status) {
      case "Done":
        return <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 16 }} />;
      case "Pending":
        return <PauseCircleOutlined style={{ color: "#b9900a", fontSize: 16 }} />;
      case "Decline":
        return <MinusCircleOutlined style={{ color: "#707070", fontSize: 16 }} />;
      case "Ongoing":
        return <SyncOutlined spin style={{ color: "#1677ff", fontSize: 16 }} />;
      default:
        return null;
    }
  };

  // ===========================
  // DFS 统计节点
  // ===========================
  const countTasks = useCallback((node) => {
    let total = 1;
    let done = node.status === "Done" ? 1 : 0;
    let decline = node.status === "Decline" ? 1 : 0;

    if (node.children) {
      node.children.forEach((ch) => {
        const r = countTasks(ch);
        total += r.total;
        done += r.done;
        decline += r.decline;
      });
    }
    return { total, done, decline };
  }, []); 

  // ===========================
  // 整体进度
  // ===========================
  const overallProgress = useMemo(() => {
    if (!taskTree.length) return 0;

    let total = 0,
      done = 0,
      decline = 0;

    taskTree.forEach((node) => {
      const r = countTasks(node);
      total += r.total;
      done += r.done;
      decline += r.decline;
    });

    return Math.round(((done + decline) / total) * 100);
  }, [taskTree, countTasks]);

  const getCalibrationContainerNode = () => {
    if (!selectedTaskId) return null;

    const selectedNode = findNode(taskTree, selectedTaskId);
    if (!selectedNode) return null;

    if (selectedNode.taskName === "Calibration") {
      return selectedNode;
    }

    const parentNode = findParentNode(taskTree, selectedTaskId);
    if (parentNode?.taskName === "Calibration") {
      return parentNode;
    }

    return null;
  };

  const getSelectedCalibrationChildNode = () => {
    if (!selectedTaskId) return null;

    const selectedNode = findNode(taskTree, selectedTaskId);
    if (!selectedNode) return null;

    const parentNode = findParentNode(taskTree, selectedTaskId);
    if (parentNode?.taskName === "Calibration" && selectedNode.taskName !== "Calibration") {
      return { node: selectedNode, parent: parentNode };
    }

    return null;
  };

  const addCalibrationChild = useCallback(
    async (calibrationContainerNode = null) => {
      const calibrationContainer = calibrationContainerNode || getCalibrationContainerNode();
      if (!calibrationContainer) {
        message.warning("请先选择 Calibration 父节点或其任一子节点");
        return;
      }

      if (!calibrationContainer.children?.length) {
        message.error("当前 Calibration 节点下没有可复制的标准子树模板");
        return;
      }

      const rawCalibrationId = window.prompt("请输入新的 CalibrationID");
      if (rawCalibrationId === null) return;

      const calibrationId = rawCalibrationId.trim();
      if (!calibrationId) {
        message.error("CalibrationID 不能为空");
        return;
      }

      if (WINDOWS_CALIBRATION_ID_PATTERN.test(calibrationId) || hasControlCharacters(calibrationId)) {
        message.error("CalibrationID 含有 Windows 非法字符");
        return;
      }

      const calibrationIds = (calibrationContainer.children || []).map((child) => child.taskName?.trim());
      if (calibrationIds.includes(calibrationId)) {
        message.error(`CalibrationID 已存在：${calibrationId}`);
        return;
      }

      const templateNode = calibrationContainer.children[0];
      const updated = JSON.parse(JSON.stringify(projectWorkFlow));
      const updatedContainer = findNode(updated.taskTree, calibrationContainer.id);
      if (!updatedContainer) {
        message.error("未找到 Calibration 父节点");
        return;
      }

      const newDetails = {};
  const clone = deepCopyCalibrationSubtree(templateNode, newDetails, calibrationId, projectWorkFlow?.taskDetails);
      updatedContainer.children = [...(updatedContainer.children || []), clone];
      updated.taskDetails = { ...updated.taskDetails, ...newDetails };

      const localResult = await createCalibrationWorkspace({ calibrationId });
      if (!localResult.success) {
        message.error(localResult.message);
        return;
      }

      const saveResult = await updateWorkFlow({
        username: user.username,
        department: user.department,
        projectId,
        projectName,
        workflow: updated,
      });

      if (!saveResult.success) {
        message.error("Calibration 目录已创建，但 workflow 保存失败");
        return;
      }

      setSelectedTaskId(clone.id);
      setExpandedKeys((prev) => Array.from(new Set([
        ...prev,
        updatedContainer.id,
        clone.id,
        ...collectSubtreeIds(clone),
      ])));
      window.location.hash = `#/task/${projectId}/${clone.id}`;
      message.success("Calibration 子节点已创建");
    },
    [createCalibrationWorkspace, getCalibrationContainerNode, message, projectId, projectName, projectWorkFlow, updateWorkFlow, user.department, user.username],
  );

  // ===========================
  // 复制 Task
  // ===========================
  const copySelectedTask = async () => {
    if (!selectedTaskId) {
      message.warning("Please select a task from the tree first");
      return;
    }

    const updated = JSON.parse(JSON.stringify(projectWorkFlow));
    const node = findNode(updated.taskTree, selectedTaskId);
    if (!node) return;

    const pos = findParentAndIndex(updated.taskTree, selectedTaskId);

    const newDetails = {};
    const clone = deepCopyTask(node, newDetails, projectWorkFlow?.taskDetails);

    updated.taskDetails = { ...updated.taskDetails, ...newDetails };

    if (pos) {
      const { siblings, index } = pos;
      siblings.splice(index + 1, 0, clone);
    } 
    else {
      // 理论上不会发生，兜底
      updated.taskTree.push(clone);
    }

    await updateWorkFlow({
      username: user.username,
      department: user.department,
      projectId: projectId,
      projectName,
      workflow: updated,
    });

    message.success("Task copied!");
  };

  // ===========================
  // 删除 Task
  // ===========================
  const deleteSelectedTask = async () => {
    if (!selectedTaskId) {
      message.warning("Please select a task from the tree first");
      return;
    }

    const updated = JSON.parse(JSON.stringify(projectWorkFlow));
    const nodeToDelete = findNode(updated.taskTree, selectedTaskId);
    if (!nodeToDelete) return;
    const idsToDelete = collectSubtreeIds(nodeToDelete);

    const removeNode = (nodes, id) => {
      return nodes.filter((node) => {
        if (node.id === id) return false;
        if (node.children) node.children = removeNode(node.children, id);
        return true;
      });
    };

    updated.taskTree = removeNode(updated.taskTree, selectedTaskId);
    if (updated.taskDetails) {
      idsToDelete.forEach((id) => {
        delete updated.taskDetails[id];
      });
    }

    const res = await updateWorkFlow({
      username: user.username,
      department: user.department,
      projectId: projectId,
      projectName,
      workflow: updated,
    });

    if (res.success) {
      setSelectedTaskId(null);
      message.success("Task deleted!");
    } else {
      message.error("Delete failed");
    }
  };

  const deleteSelectedCalibrationChild = () => {
    const calibrationChild = getSelectedCalibrationChildNode();
    if (!calibrationChild) {
      message.warning("请先选择 Calibration 下的子节点");
      return;
    }

    Modal.confirm({
      title: "删除 Calibration 子节点？",
      content: "默认只删除 workflow 节点，不会删除本地文件夹，避免误删 email、结果和报告。",
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: deleteSelectedTask,
    });
  };

  // ===========================
  // TreeData
  // ===========================
  const treeData = useMemo(() => {
    const renderNodeTitle = (item) => {
      const isCalibrationContainer = item.taskName === "Calibration";
      const isSelectedCalibrationChild =
        selectedTaskId === item.id &&
        item.taskName !== "Calibration" &&
        findParentNode(taskTree, item.id)?.taskName === "Calibration";

      return (
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span>{item.taskName}</span>
          {isCalibrationContainer && (
            <Button
              type="text"
              size="small"
              onClick={(event) => {
                event.stopPropagation();
                addCalibrationChild(item);
              }}
              style={{ minWidth: 18, padding: 0, height: 18, lineHeight: "18px", fontWeight: 700, color: "#1677ff" }}
            >
              +
            </Button>
          )}
          {isSelectedCalibrationChild && (
            <Button
              type="text"
              size="small"
              onClick={(event) => {
                event.stopPropagation();
                deleteSelectedCalibrationChild();
              }}
              style={{ minWidth: 18, padding: 0, height: 18, lineHeight: "18px", fontWeight: 700, color: "#d4380d" }}
            >
              -
            </Button>
          )}
        </span>
      );
    };

    const convert = (nodes) =>
      nodes.map((item) => ({
        key: item.id,
        icon: getStatusIcon(item.status),
        title: renderNodeTitle(item),
        children: item.children ? convert(item.children) : [],
      }));

    return convert(taskTree);
  }, [addCalibrationChild, deleteSelectedCalibrationChild, selectedTaskId, taskTree]);

  const getAllKeys = (nodes) => {
    const keys = [];
    const dfs = (items) => {
      items.forEach((item) => {
        keys.push(item.id);
        if (item.children?.length) dfs(item.children);
      });
    };
    dfs(nodes);
    return keys;
  };

  // ===========================
  // ⭐ 初次加载自动展开全部
  // ===========================
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [initialized, setInitialized] = useState(false);

  const syncSelectedTaskFromHash = useCallback(() => {
    const match = window.location.hash.match(/#\/task\/[^/]+\/([^/?#]+)/);
    setSelectedTaskId(match ? decodeURIComponent(match[1]) : null);
  }, []);

  useEffect(() => {
    if (!initialized && taskTree.length > 0) {
      setExpandedKeys(getAllKeys(taskTree));
      setInitialized(true);
    }
  }, [taskTree, initialized]);

  useEffect(() => {
    syncSelectedTaskFromHash();
    window.addEventListener("hashchange", syncSelectedTaskFromHash);

    return () => {
      window.removeEventListener("hashchange", syncSelectedTaskFromHash);
    };
  }, [syncSelectedTaskFromHash]);

  const onExpand = (keys) => {
    setExpandedKeys(keys); // 用户折叠/展开后更新
  };

  // ===========================
  // UI
  // ===========================
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, height: "100%" }}>

      {/* 顶部标题 + 按钮 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={4} style={{ margin: 0 }}>Project Detail</Title>

        <div style={{ display: "flex", gap: 10 }}>
          {getCalibrationContainerNode() && (
            <Tooltip title="Add Calibration Child">
              <Button
                type="text"
                size="small"
                onClick={addCalibrationChild}
                style={{ minWidth: 24, padding: 0, fontWeight: 700, color: "#389e0d" }}
              >
                +
              </Button>
            </Tooltip>
          )}

          {getSelectedCalibrationChildNode() && (
            <Tooltip title="Delete Calibration Child">
              <Button
                type="text"
                size="small"
                onClick={deleteSelectedCalibrationChild}
                style={{ minWidth: 24, padding: 0, fontWeight: 700, color: "#d4380d" }}
              >
                -
              </Button>
            </Tooltip>
          )}

          <Tooltip title="Copy Selected Task">
            <CopyOutlined style={{ fontSize: 15, cursor: "pointer" }} onClick={copySelectedTask} />
          </Tooltip>

          <Tooltip title="Delete Selected Task">
            <DeleteOutlined style={{ fontSize: 15, color: "#ff0101", cursor: "pointer" }} onClick={deleteSelectedTask} />
          </Tooltip>
        </div>
      </div>

      <Space direction="vertical" size={4} style={{ width: "100%" }}>
        <Text type="secondary" style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 4 }}>
          <ProjectOutlined /> Whole Project Progress
        </Text>
        <ProgressBar percent={overallProgress} />
      </Space>

      <div style={{ overflow: "auto", flex: 1 }}>
        <Tree
          showIcon
          expandedKeys={expandedKeys}
          onExpand={onExpand}
          treeData={treeData}
          onSelect={(keys, info) => {
            const uuid = info.node.key;
            setSelectedTaskId(uuid);
            window.location.hash = `#/task/${projectId}/${uuid}`;
          }}
        />
      </div>
    </div>
  );
}
