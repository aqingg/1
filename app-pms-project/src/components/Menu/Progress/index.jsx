import React, { useMemo, useState, useEffect, useCallback } from "react";
import { Typography, Tree, Space, message, Tooltip, Button } from "antd";
import {
  CheckCircleOutlined,
  PauseCircleOutlined,
  MinusCircleOutlined,
  SyncOutlined,
  ProjectOutlined,
  CopyOutlined,
  DeleteOutlined,
} from "@ant-design/icons";

import ProgressBar from "../ProgressBar";
import { useAppContext } from "../../../context/AppContext";

const { Title, Text } = Typography;

const WINDOWS_CALIBRATION_ID_PATTERN = /[<>:"/\\|?*]/;

const clonePlain = (value) => {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value));
};

const uuid = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const hasControlCharacters = (value) =>
  Array.from(value || "").some((character) => character.charCodeAt(0) < 32);

const isCalibrationNodeName = (name) =>
  String(name || "").trim().toLowerCase() === "calibration";

const collectSubtreeIds = (task, collected = []) => {
  if (!task) return collected;

  collected.push(task.id);

  if (Array.isArray(task.children)) {
    task.children.forEach((child) => collectSubtreeIds(child, collected));
  }

  return collected;
};

const findNode = (nodes, id) => {
  if (!Array.isArray(nodes)) return null;

  for (const node of nodes) {
    if (node.id === id) return node;

    if (Array.isArray(node.children) && node.children.length > 0) {
      const result = findNode(node.children, id);
      if (result) return result;
    }
  }

  return null;
};

const findParentNode = (nodes, id, parent = null) => {
  if (!Array.isArray(nodes)) return null;

  for (const node of nodes) {
    if (node.id === id) return parent;

    if (Array.isArray(node.children) && node.children.length > 0) {
      const result = findParentNode(node.children, id, node);
      if (result) return result;
    }
  }

  return null;
};

const findParentAndIndex = (nodes, id, parent = null) => {
  if (!Array.isArray(nodes)) return null;

  for (let index = 0; index < nodes.length; index += 1) {
    const node = nodes[index];

    if (node.id === id) {
      return {
        parent,
        index,
        siblings: nodes,
      };
    }

    if (Array.isArray(node.children) && node.children.length > 0) {
      const result = findParentAndIndex(node.children, id, node);
      if (result) return result;
    }
  }

  return null;
};

const removeNodeById = (nodes, id) => {
  if (!Array.isArray(nodes)) return [];

  return nodes
    .filter((node) => node.id !== id)
    .map((node) => {
      if (!Array.isArray(node.children)) return node;

      return {
        ...node,
        children: removeNodeById(node.children, id),
      };
    });
};

const getAllKeys = (nodes) => {
  const keys = [];

  const dfs = (items) => {
    if (!Array.isArray(items)) return;

    items.forEach((item) => {
      keys.push(item.id);

      if (Array.isArray(item.children) && item.children.length > 0) {
        dfs(item.children);
      }
    });
  };

  dfs(nodes);
  return keys;
};

const deepCopyTask = (task, newDetails, taskDetails) => {
  const newId = uuid();
  const sourceDetail = taskDetails?.[task.id];

  if (sourceDetail) {
    newDetails[newId] = {
      ...clonePlain(sourceDetail),
      taskName: `${sourceDetail.taskName || task.taskName} (Copy)`,
    };
  }

  return {
    ...clonePlain(task),
    id: newId,
    status: "Pending",
    children: Array.isArray(task.children)
      ? task.children.map((child) => deepCopyTask(child, newDetails, taskDetails))
      : [],
  };
};

const deepCopyCalibrationSubtree = (
  task,
  newDetails,
  rootTaskName,
  taskDetails
) => {
  const newId = uuid();
  const originalDetail = taskDetails?.[task.id];

  if (originalDetail) {
    newDetails[newId] = {
      ...clonePlain(originalDetail),
      taskName: rootTaskName,
    };
  } else {
    newDetails[newId] = {
      taskName: rootTaskName,
    };
  }

  return {
    ...clonePlain(task),
    id: newId,
    taskName: rootTaskName,
    status: "Pending",
    children: Array.isArray(task.children)
      ? task.children.map((child) =>
          deepCopyCalibrationSubtree(
            child,
            newDetails,
            child.taskName,
            taskDetails
          )
        )
      : [],
  };
};

export default function Progress() {
  const {
    projectWorkFlow,
    updateWorkFlow,
    user,
    projectName,
    projectId,
    createCalibrationWorkspace,
  } = useAppContext();

  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [initialized, setInitialized] = useState(false);

  const taskTree = useMemo(
    () => projectWorkFlow?.taskTree || [],
    [projectWorkFlow?.taskTree]
  );

  const getStatusIcon = useCallback((status) => {
    switch (status) {
      case "Done":
        return <CheckCircleOutlined style={{ color: "#52c41a" }} />;
      case "Pending":
        return <PauseCircleOutlined style={{ color: "#8c8c8c" }} />;
      case "Decline":
        return <MinusCircleOutlined style={{ color: "#ff4d4f" }} />;
      case "Ongoing":
        return <SyncOutlined spin style={{ color: "#1677ff" }} />;
      default:
        return <ProjectOutlined style={{ color: "#8c8c8c" }} />;
    }
  }, []);

  const countTasks = useCallback((node) => {
    let total = 1;
    let done = node.status === "Done" ? 1 : 0;
    let decline = node.status === "Decline" ? 1 : 0;

    if (Array.isArray(node.children)) {
      node.children.forEach((child) => {
        const result = countTasks(child);
        total += result.total;
        done += result.done;
        decline += result.decline;
      });
    }

    return { total, done, decline };
  }, []);

  const overallProgress = useMemo(() => {
    if (!taskTree.length) return 0;

    let total = 0;
    let done = 0;
    let decline = 0;

    taskTree.forEach((node) => {
      const result = countTasks(node);
      total += result.total;
      done += result.done;
      decline += result.decline;
    });

    if (total === 0) return 0;
    return Math.round(((done + decline) / total) * 100);
  }, [taskTree, countTasks]);

  const getCalibrationContainerNode = useCallback(() => {
    if (!selectedTaskId) return null;

    const selectedNode = findNode(taskTree, selectedTaskId);
    if (!selectedNode) return null;

    if (isCalibrationNodeName(selectedNode.taskName)) {
      return selectedNode;
    }

    const parentNode = findParentNode(taskTree, selectedTaskId);
    if (isCalibrationNodeName(parentNode?.taskName)) {
      return parentNode;
    }

    return null;
  }, [selectedTaskId, taskTree]);

  const getSelectedCalibrationChildNode = useCallback(() => {
    if (!selectedTaskId) return null;

    const selectedNode = findNode(taskTree, selectedTaskId);
    if (!selectedNode) return null;

    const parentNode = findParentNode(taskTree, selectedTaskId);

    if (
      isCalibrationNodeName(parentNode?.taskName) &&
      !isCalibrationNodeName(selectedNode.taskName)
    ) {
      return {
        node: selectedNode,
        parent: parentNode,
      };
    }

    return null;
  }, [selectedTaskId, taskTree]);

  const addCalibrationChild = useCallback(
    async (calibrationContainerNode = null) => {
      const calibrationContainer =
        calibrationContainerNode || getCalibrationContainerNode();

      if (!calibrationContainer) {
        message.warning("请先选择 Calibration 父节点或其任一子节点");
        return;
      }

      if (
        !Array.isArray(calibrationContainer.children) ||
        calibrationContainer.children.length === 0
      ) {
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

      if (
        WINDOWS_CALIBRATION_ID_PATTERN.test(calibrationId) ||
        hasControlCharacters(calibrationId) ||
        calibrationId === "." ||
        calibrationId === ".."
      ) {
        message.error('CalibrationID 含有 Windows 非法字符，不能包含 <>:"/\\|?*');
        return;
      }

      const calibrationIds = (calibrationContainer.children || []).map((child) =>
        child.taskName?.trim()
      );

      if (calibrationIds.includes(calibrationId)) {
        message.error(`CalibrationID 已存在：${calibrationId}`);
        return;
      }

      const updated = clonePlain(projectWorkFlow);
      const updatedContainer = findNode(updated.taskTree, calibrationContainer.id);

      if (!updatedContainer) {
        message.error("未找到 Calibration 父节点");
        return;
      }

      const templateNode = calibrationContainer.children[0];
      const newDetails = {};
      const clone = deepCopyCalibrationSubtree(
        templateNode,
        newDetails,
        calibrationId,
        projectWorkFlow?.taskDetails
      );

      updatedContainer.children = [...(updatedContainer.children || []), clone];
      updated.taskDetails = {
        ...(updated.taskDetails || {}),
        ...newDetails,
      };

      const localResult = await createCalibrationWorkspace({ calibrationId });

      if (!localResult?.success) {
        message.error(localResult?.message || "创建本地 Calibration 文件夹失败");
        return;
      }

      const saveResult = await updateWorkFlow({
        username: user.username,
        department: user.department,
        projectId,
        projectName,
        workflow: updated,
      });

      if (!saveResult?.success) {
        message.error("Calibration 目录已创建，但 workflow 保存失败");
        return;
      }

      setSelectedTaskId(clone.id);
      setExpandedKeys((prev) =>
        Array.from(
          new Set([
            ...prev,
            updatedContainer.id,
            clone.id,
            ...collectSubtreeIds(clone),
          ])
        )
      );

      window.location.hash = `#/task/${projectId}/${clone.id}`;
      message.success("Calibration 子节点已创建");
    },
    [
      createCalibrationWorkspace,
      getCalibrationContainerNode,
      projectId,
      projectName,
      projectWorkFlow,
      updateWorkFlow,
      user.department,
      user.username,
    ]
  );

  const copySelectedTask = useCallback(async () => {
    if (!selectedTaskId) {
      message.warning("Please select a task from the tree first");
      return;
    }

    const updated = clonePlain(projectWorkFlow);
    const node = findNode(updated.taskTree, selectedTaskId);

    if (!node) {
      message.error("未找到当前选中的节点");
      return;
    }

    const pos = findParentAndIndex(updated.taskTree, selectedTaskId);
    const newDetails = {};
    const clone = deepCopyTask(node, newDetails, projectWorkFlow?.taskDetails);

    updated.taskDetails = {
      ...(updated.taskDetails || {}),
      ...newDetails,
    };

    if (pos) {
      const { siblings, index } = pos;
      siblings.splice(index + 1, 0, clone);
    } else {
      updated.taskTree.push(clone);
    }

    const res = await updateWorkFlow({
      username: user.username,
      department: user.department,
      projectId,
      projectName,
      workflow: updated,
    });

    if (res?.success) {
      message.success("Task copied!");
    } else {
      message.error("Copy failed");
    }
  }, [
    projectId,
    projectName,
    projectWorkFlow,
    selectedTaskId,
    updateWorkFlow,
    user.department,
    user.username,
  ]);

  const deleteTaskById = useCallback(
    async (taskIdToDelete, successMessage = "Task deleted!") => {
      if (!taskIdToDelete) {
        message.warning("Please select a task from the tree first");
        return;
      }

      const updated = clonePlain(projectWorkFlow);
      const nodeToDelete = findNode(updated.taskTree, taskIdToDelete);

      if (!nodeToDelete) {
        message.error("未找到要删除的节点");
        return;
      }

      const parent = findParentNode(updated.taskTree, taskIdToDelete);
      const idsToDelete = collectSubtreeIds(nodeToDelete);

      updated.taskTree = removeNodeById(updated.taskTree, taskIdToDelete);

      if (updated.taskDetails) {
        idsToDelete.forEach((id) => {
          delete updated.taskDetails[id];
        });
      }

      const res = await updateWorkFlow({
        username: user.username,
        department: user.department,
        projectId,
        projectName,
        workflow: updated,
      });

      if (res?.success) {
        const nextSelectedId = parent?.id || null;
        setSelectedTaskId(nextSelectedId);

        if (nextSelectedId) {
          window.location.hash = `#/task/${projectId}/${nextSelectedId}`;
        } else {
          window.location.hash = `#/project/${projectId}`;
        }

        message.success(successMessage);
      } else {
        message.error("Delete failed");
      }
    },
    [
      projectId,
      projectName,
      projectWorkFlow,
      updateWorkFlow,
      user.department,
      user.username,
    ]
  );

  const deleteSelectedTask = useCallback(() => {
    if (!selectedTaskId) {
      message.warning("Please select a task from the tree first");
      return;
    }

    const ok = window.confirm(
      "确认删除当前选中的 workflow 节点？\n\n注意：这个操作不会删除本地文件夹。"
    );

    if (!ok) return;

    deleteTaskById(selectedTaskId);
  }, [deleteTaskById, selectedTaskId]);

  const deleteCalibrationChildById = useCallback(
    async (nodeId) => {
      const node = findNode(taskTree, nodeId);
      const parent = findParentNode(taskTree, nodeId);

      if (!node) {
        message.error("未找到要删除的 Calibration 节点");
        return;
      }

      if (!isCalibrationNodeName(parent?.taskName)) {
        message.warning("只能删除 Calibration 下的一级子节点");
        return;
      }

      const ok = window.confirm(
        `确认删除 Calibration 子节点 "${node.taskName}" 吗？\n\n只会删除 workflow 节点，不会删除本地文件夹。`
      );

      if (!ok) return;

      await deleteTaskById(nodeId, "Calibration 子节点已删除");
    },
    [deleteTaskById, taskTree]
  );

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

  const onExpand = useCallback((keys) => {
    setExpandedKeys(keys);
  }, []);

  const treeData = useMemo(() => {
    const stopTreeEvent = (event) => {
      event.preventDefault();
      event.stopPropagation();
    };

    const renderNodeTitle = (item) => {
      const isCalibrationContainer = isCalibrationNodeName(item.taskName);
      const parentNode = findParentNode(taskTree, item.id);
      const isCalibrationDirectChild =
        isCalibrationNodeName(parentNode?.taskName) &&
        !isCalibrationNodeName(item.taskName);

      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span>{item.taskName}</span>

          {isCalibrationContainer && (
            <Tooltip title="Add CalibrationID">
              <Button
                type="text"
                size="small"
                onMouseDown={stopTreeEvent}
                onClick={(event) => {
                  stopTreeEvent(event);
                  addCalibrationChild(item);
                }}
                style={{
                  minWidth: 18,
                  padding: 0,
                  height: 18,
                  lineHeight: "18px",
                  fontWeight: 700,
                  color: "#1677ff",
                }}
              >
                +
              </Button>
            </Tooltip>
          )}

          {isCalibrationDirectChild && (
            <Tooltip title="Delete this CalibrationID from workflow only">
              <Button
                type="text"
                size="small"
                onMouseDown={stopTreeEvent}
                onClick={(event) => {
                  stopTreeEvent(event);
                  deleteCalibrationChildById(item.id);
                }}
                style={{
                  minWidth: 18,
                  padding: 0,
                  height: 18,
                  lineHeight: "18px",
                  fontWeight: 700,
                  color: "#d4380d",
                }}
              >
                -
              </Button>
            </Tooltip>
          )}
        </span>
      );
    };

    const convert = (nodes) =>
      nodes.map((item) => ({
        key: item.id,
        icon: getStatusIcon(item.status),
        title: renderNodeTitle(item),
        children: Array.isArray(item.children) ? convert(item.children) : [],
      }));

    return convert(taskTree);
  }, [
    addCalibrationChild,
    deleteCalibrationChildById,
    getStatusIcon,
    taskTree,
  ]);

  const selectedCalibrationChild = getSelectedCalibrationChildNode();
  const calibrationContainer = getCalibrationContainerNode();

  return (
    <>
      <Space
        style={{
          width: "100%",
          justifyContent: "space-between",
          marginBottom: 8,
        }}
        align="center"
      >
        <Title level={5} style={{ margin: 0 }}>
          Project Detail
        </Title>

        <Space size={4}>
          {calibrationContainer && (
            <Tooltip title="Add CalibrationID">
              <Button
                type="text"
                size="small"
                onClick={() => addCalibrationChild(calibrationContainer)}
                style={{
                  fontWeight: 700,
                  color: "#1677ff",
                }}
              >
                +
              </Button>
            </Tooltip>
          )}

          {selectedCalibrationChild && (
            <Tooltip title="Delete selected CalibrationID from workflow only">
              <Button
                type="text"
                size="small"
                onClick={() =>
                  deleteCalibrationChildById(selectedCalibrationChild.node.id)
                }
                style={{
                  fontWeight: 700,
                  color: "#d4380d",
                }}
              >
                -
              </Button>
            </Tooltip>
          )}

          <Tooltip title="Copy selected task">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={copySelectedTask}
            />
          </Tooltip>

          <Tooltip title="Delete selected task">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={deleteSelectedTask}
            />
          </Tooltip>
        </Space>
      </Space>

      <div style={{ marginBottom: 12 }}>
        <Text type="secondary">Whole Project Progress</Text>
        <ProgressBar percent={overallProgress} />
      </div>

      <Tree
        showIcon
        blockNode
        expandedKeys={expandedKeys}
        selectedKeys={selectedTaskId ? [selectedTaskId] : []}
        treeData={treeData}
        onExpand={onExpand}
        onSelect={(keys, info) => {
          const selectedId = info.node.key;
          setSelectedTaskId(selectedId);
          window.location.hash = `#/task/${projectId}/${selectedId}`;
        }}
      />
    </>
  );
}