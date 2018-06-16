#include <Python.h>
#include <linux/tcp.h>

static PyObject* persist_state(PyObject* self, PyObject* args)
{
  int fd;
  if(!PyArg_ParseTuple(args, "i", &fd)) {
    return NULL;
  }
  int val = MPTCP_INFO_FLAG_SAVE_MASTER;
  setsockopt(fd, SOL_TCP, MPTCP_INFO, &val, sizeof(val));
  return Py_BuildValue("i", fd);
}

static PyObject* get_info(PyObject* self, PyObject* args)
{
  int fd;
  if(!PyArg_ParseTuple(args, "i", &fd)) {
    return NULL;
  }

  struct mptcp_info minfo;
  struct mptcp_meta_info meta_info;
  struct tcp_info initial;
  struct tcp_info others[NUM_SUBFLOWS];
  struct mptcp_sub_info others_info[NUM_SUBFLOWS];

  minfo.tcp_info_len = sizeof(struct tcp_info);
  minfo.sub_len = sizeof(others);
  minfo.meta_len = sizeof(struct mptcp_meta_info);
  minfo.meta_info = &meta_info;
  minfo.initial = &initial;
  minfo.subflows = &others;
  minfo.sub_info_len = sizeof(struct mptcp_sub_info);
  minfo.total_sub_info_len = sizeof(others_info);
  minfo.subflow_info = &others_info;

  socklen_t len = sizeof(minfo);

  getsockopt(fd, SOL_TCP, MPTCP_INFO, &minfo, &len);

  PyObject *list = PyList_New(0);
  PyList_Append(list, Py_BuildValue("I", others[0].tcpi_bytes_received));
  PyList_Append(list, Py_BuildValue("I", others[1].tcpi_bytes_received));
  PyList_Append(list, Py_BuildValue("I", meta_info.mptcpi_recv_ofo_buff));
  return list;
}


static PyMethodDef Methods[] = {
  {"persist_state", persist_state, METH_VARARGS, "persist mptcp subflows tate"},
  {"get_info", get_info, METH_VARARGS, "get recv info"},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef Def = {
  PyModuleDef_HEAD_INIT,
  "info",
  "get recv info",
  -1,
  Methods
};

PyMODINIT_FUNC PyInit_mpsched(void)
{
  return PyModule_Create(&Def);
}
