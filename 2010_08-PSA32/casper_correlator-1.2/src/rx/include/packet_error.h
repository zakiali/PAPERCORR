#ifndef PACKET_ERROR_H
#define PACKET_ERROR_H

#include <string>

class PacketError {
  private:
    std::string msg;
  public:
    PacketError(const std::string &message) : msg (message) {}
    const char* get_message() const { return msg.c_str(); }
};

#endif
