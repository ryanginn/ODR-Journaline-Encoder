#include <cstdio>
#include <vector>
#include <sys/time.h>
#include "dabdatagroupdecoder.h"
#include "newsobject.h"
#include "NML.h"
static void cb(const DAB_DATAGROUP_DECODER_msc_datagroup_header_t *hdr, const unsigned long len, const unsigned char *buf, void *) {
  if (hdr->datagroup_type != 0) { printf("DG type %d len %lu (skipped)\n", hdr->datagroup_type, len); return; }
  struct timeval t; gettimeofday(&t, NULL);
  unsigned char buffer[8192]; unsigned long n = 0;
  NewsObject no(len, buf, &t); no.copyNml(&n, buffer);
  NML::RawNewsObject_t raw; raw.nml_len = n; raw.extended_header_len = 0;
  for (unsigned long i = 0; i < n; i++) raw.nml[i] = buffer[i];
  RemoveNMLEscapeSequences rm; NMLFactory f;
  NML *x = f.CreateNML(raw, &rm);
  printf("OBJ valid=%d id=%04x type=%s static=%d rev=%d title=[%s] items=%u\n", x->isValid(), x->GetObjectId(), x->GetObjectTypeString(), x->isStatic(), x->GetRevisionIndex(), x->GetTitle().c_str(), x->GetNrOfItems());
  for (unsigned i = 0; i < x->GetNrOfItems(); i++) printf("  item link=%04x [%s]\n", x->GetLinkId(i), x->GetItemText(i).c_str());
  if (!x->isValid()) printf("%s\n", x->Dump().c_str());
  delete x;
}
int main(int argc, char **argv) {
  FILE *fp = fopen(argv[1], "rb");
  DAB_DATAGROUP_DECODER_t d = DAB_DATAGROUP_DECODER_createDec(cb, NULL);
  unsigned char lb[2];
  while (fread(lb, 1, 2, fp) == 2) {
    unsigned n = (lb[0] << 8) | lb[1]; std::vector<unsigned char> b(n);
    if (fread(b.data(), 1, n, fp) != n) break;
    long r = DAB_DATAGROUP_DECODER_putData(d, n, b.data());
    if (r < 0) printf("putData error %ld\n", r);
  }
  return 0;
}
