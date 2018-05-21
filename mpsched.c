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

static PyObject* get_meta_info(PyObject* self, PyObject* args)
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
    PyList_Append(list, Py_BuildValue("I", meta_info.mptcpi_unacked));
    PyList_Append(list, Py_BuildValue("I", meta_info.mptcpi_retransmits));
    return list;
}

static PyObject* get_sub_info(PyObject* self, PyObject* args)
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
  int i;
  for(i=0; i < NUM_SUBFLOWS; i++){

    if(others[i].tcpi_state != 1)
      break;

    PyObject *subflows = PyList_New(0);
    PyList_Append(subflows, Py_BuildValue("I", others[i].tcpi_segs_out));
    PyList_Append(subflows, Py_BuildValue("I", others[i].tcpi_rtt));
    PyList_Append(subflows, Py_BuildValue("I", others[i].tcpi_snd_cwnd));
    //PyList_Append(subflows, Py_BuildValue("I", others[i].tcpi_unacked));
    //PyList_Append(subflows, Py_BuildValue("I", others[i].tcpi_total_retrans)); /* Packets which are "in flight"	*/

    PyList_Append(list, subflows);
  }
  return list;
}


static PyObject* set_seg(PyObject* self, PyObject* args)
{
  PyObject * listObj;
  if (! PyArg_ParseTuple( args, "O", &listObj ))
    return NULL;

  long length = PyList_Size(listObj);
  int fd = (int)PyLong_AsLong(PyList_GetItem(listObj, 0));
  int i;

  struct mptcp_sched_info sched_info;
  sched_info.len = length-1;
  unsigned char quota[NUM_SUBFLOWS];
  unsigned char segments[NUM_SUBFLOWS];

  sched_info.quota = &quota;
  sched_info.num_segments = &segments;

  for(i=1; i<length; i++) {
    PyObject* temp = PyList_GetItem(listObj, i);
    long elem = PyLong_AsLong(temp);

    segments[i-1] = (unsigned char) elem;
  }

  setsockopt(fd, SOL_TCP, MPTCP_SCHED_INFO, &sched_info, sizeof(sched_info));

  return Py_BuildValue("i", fd);
}

static PyMethodDef Methods[] = {
  {"persist_state", persist_state, METH_VARARGS, "persist mptcp subflows tate"},
  {"get_meta_info", get_meta_info, METH_VARARGS, "get mptcp recv buff size"},
  {"get_sub_info", get_sub_info, METH_VARARGS, "get mptcp subflows info"},
  {"set_seg", set_seg, METH_VARARGS, "set num of segments in all mptcp subflows"},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef Def = {
  PyModuleDef_HEAD_INIT,
  "mpsched",
  "mpctp scheduler \"mysched\" adjuset args",
  -1,
  Methods
};

PyMODINIT_FUNC PyInit_mpsched(void)
{
  return PyModule_Create(&Def);
}
