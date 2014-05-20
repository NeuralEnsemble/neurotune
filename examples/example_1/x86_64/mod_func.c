#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;
modl_reg(){
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");

    fprintf(stderr," Kv_3_erisir_99.mod");
    fprintf(stderr," kv_1.mod");
    fprintf(stderr," na.mod");
    fprintf(stderr, "\n");
  }
  _Kv_3_erisir_99_reg();
  _kv_1_reg();
  _na_reg();
}
